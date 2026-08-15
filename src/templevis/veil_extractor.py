"""
Veil Extractor Module

Extracts veil (V) and endowment officiator (EO) assignments from a temple
worker schedule PDF using the geometry of the shaded assignment boxes.

Unlike the INI extraction in :mod:`templevis.table_processor`, the veil codes
are printed once inside a shaded box that spans the whole assignment window, so
the start/end times come from the box rectangle rather than the table cells.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime

import pdfplumber

# Assignment code words such as 'V-3', 'EO-2', 'V-2TR' or 'V-A'.
# The PDF uses an en dash and occasionally doubles it ('V--4').
CODE_PATTERN = re.compile(
    r'^(V|EO)\s*[-\u2013\u2014]+\s*(\d+|[A-Za-z])\s*([A-Za-z]*)$'
)

# Hour labels in the table header, e.g. '05:00'.
HOUR_PATTERN = re.compile(r'^(\d{1,2}):(\d{2})$')

# Schedule date in the page header, e.g. '5 Aug 2026'.
DATE_PATTERN = re.compile(r'\b(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})\b')

HEADER_BAND_BOTTOM = 90  # Header hour labels sit above this y coordinate.
NAME_COLUMN_RIGHT = 200  # Assignment columns start at ~x=205.
NAME_COLUMN_LEFT = 40    # Skip the row-number column.
ROW_TOLERANCE = 5        # Vertical tolerance when grouping words into rows.
SESSION_START_TOLERANCE = 30  # Minutes a printed session time may precede its box.
TRAINEE_VARIANT = 'TR'   # Trainees shadow a session and are not counted as presenters.


@dataclass(frozen=True)
class VeilAssignment:
    """A single shaded assignment box for one worker."""

    name: str
    kind: str            # 'V' or 'EO'
    code: str            # e.g. 'V-3' or 'V-2TR'
    slot: str            # Session number, or a letter for non-session codes
    variant: str         # Trailing marker such as 'TR' for a trainee
    start_minutes: int   # Minutes since midnight
    end_minutes: int
    page: int

    def covers(self, minutes):
        """True when the given time-of-day falls inside the assignment box."""
        return self.start_minutes <= minutes < self.end_minutes

    @property
    def start_time(self):
        return _format_minutes(self.start_minutes)

    @property
    def end_time(self):
        return _format_minutes(self.end_minutes)


def _format_minutes(minutes):
    hour, minute = divmod(minutes, 60)
    suffix = 'AM' if hour < 12 else 'PM'
    display_hour = hour % 12 or 12
    return f"{display_hour}:{minute:02d} {suffix}"


def parse_time_of_day(text):
    """Parse a schedule time such as '6:05' or '6:05 Veil' into minutes.

    Schedule times are evening shift times, so hours before noon are PM.
    """
    match = re.search(r'(\d{1,2}):(\d{2})', str(text))
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour < 12:
        hour += 12
    return hour * 60 + minute


class VeilPDFExtractor:
    """Reads veil and EO assignments out of a schedule PDF."""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.assignments = []
        self.schedule_date = None

    def extract(self):
        """Extract all V and EO assignments from the PDF.

        Returns:
            list[VeilAssignment]: assignments sorted by start time then name.
        """
        found = {}
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words()

                if self.schedule_date is None:
                    self.schedule_date = self._extract_date(words)

                axis = self._build_time_axis(words)
                if axis is None:
                    continue

                rows = self._build_name_rows(words)
                if not rows:
                    continue

                rects = [r for r in page.rects if r.get('fill')]

                for word in words:
                    match = CODE_PATTERN.match(word['text'].strip())
                    if not match:
                        continue

                    name = self._name_for_word(word, rows)
                    if not name:
                        continue

                    box = self._enclosing_rect(word, rects)
                    if box is None:
                        continue

                    start = _round_to_five(axis(box['x0']))
                    end = _round_to_five(axis(box['x1']))
                    if end <= start:
                        continue

                    kind, slot, variant = match.groups()
                    slot = slot.upper()
                    variant = variant.upper()
                    assignment = VeilAssignment(
                        name=name,
                        kind=kind,
                        code=f"{kind}-{slot}{variant}",
                        slot=slot,
                        variant=variant,
                        start_minutes=start,
                        end_minutes=end,
                        page=page_num,
                    )
                    found[(name, assignment.code, start)] = assignment

        self.assignments = sorted(
            found.values(), key=lambda a: (a.start_minutes, a.name)
        )
        return self.assignments

    def presenters_at(self, minutes, kind='V'):
        """Names whose assignment box of the given kind covers a time.

        Args:
            minutes: Time of day in minutes since midnight.
            kind: 'V' for veil presenters, 'EO' for endowment officiators.

        Returns:
            list[str]: unique names sorted alphabetically.
        """
        if not self.assignments:
            self.extract()

        names = {
            a.name
            for a in self.assignments
            if a.kind == kind and a.covers(minutes)
        }
        return sorted(names, key=lambda n: n.lower())

    def session_at(self, minutes, start_tolerance=SESSION_START_TOLERANCE):
        """Resolve one veil session to its presenters and officiator.

        The veil box that contains the session time identifies the session. If
        no box contains it, the next box starting within ``start_tolerance``
        minutes is used, which covers sheets whose printed session time is a
        few minutes ahead of the assignment window.

        Returns:
            dict with 'code', 'start_minutes', 'end_minutes', 'presenters'
            (list[str]) and 'officiator' (str or None), or None when no veil
            box matches.
        """
        if not self.assignments:
            self.extract()

        veil = [
            a for a in self.assignments
            if a.kind == 'V' and a.slot.isdigit() and a.variant != TRAINEE_VARIANT
        ]
        matches = [a for a in veil if a.covers(minutes)]

        if not matches:
            upcoming = [
                a for a in veil
                if 0 < a.start_minutes - minutes <= start_tolerance
            ]
            if not upcoming:
                return None
            first_start = min(a.start_minutes for a in upcoming)
            matches = [a for a in upcoming if a.start_minutes == first_start]

        slot = matches[0].slot
        presenters = sorted(
            {a.name for a in matches if a.slot == slot}, key=lambda n: n.lower()
        )

        # The EO box for a session carries the same code number as the veil box.
        officiators = sorted(
            {a.name for a in self.assignments if a.kind == 'EO' and a.slot == slot},
            key=lambda n: n.lower(),
        )

        return {
            'code': f"V-{slot}",
            'start_minutes': matches[0].start_minutes,
            'end_minutes': matches[0].end_minutes,
            'presenters': presenters,
            'officiator': officiators[0] if officiators else None,
        }

    def _extract_date(self, words):
        header = ' '.join(
            w['text'] for w in words if w['top'] < HEADER_BAND_BOTTOM
        )
        match = DATE_PATTERN.search(header)
        if not match:
            return None
        try:
            parsed = datetime.strptime(
                f"{match.group(1)} {match.group(2)[:3].title()} {match.group(3)}",
                '%d %b %Y',
            )
        except ValueError:
            return None
        return date(parsed.year, parsed.month, parsed.day)

    def _build_time_axis(self, words):
        """Return a function mapping an x coordinate to minutes since midnight."""
        points = []
        for word in words:
            if word['top'] >= HEADER_BAND_BOTTOM:
                continue
            match = HOUR_PATTERN.match(word['text'].strip())
            if not match:
                continue
            hour, minute = int(match.group(1)), int(match.group(2))
            if hour < 12:
                hour += 12
            points.append((word['x0'], hour * 60 + minute))

        if len(points) < 2:
            return None

        slope, intercept = _fit_line(points)
        if slope <= 0:
            return None

        # Drop header labels that were mis-extracted before the final fit.
        kept = [p for p in points if abs(slope * p[0] + intercept - p[1]) <= 2]
        if len(kept) >= 2:
            slope, intercept = _fit_line(kept)

        return lambda x: slope * x + intercept

    def _build_name_rows(self, words):
        """Group name-column words into (center_y, name) row entries."""
        candidates = [
            w for w in words
            if NAME_COLUMN_LEFT <= w['x0'] and w['x1'] <= NAME_COLUMN_RIGHT
            and w['top'] >= HEADER_BAND_BOTTOM
        ]
        candidates.sort(key=lambda w: (w['top'], w['x0']))

        rows = []
        current = []
        for word in candidates:
            if current and abs(word['top'] - current[0]['top']) > ROW_TOLERANCE:
                rows.append(current)
                current = []
            current.append(word)
        if current:
            rows.append(current)

        entries = []
        for row in rows:
            text = ' '.join(w['text'] for w in row).strip()
            if ',' not in text:
                continue
            name = re.sub(r'\s+', ' ', text)
            last_name, first_name = name.split(',', 1)
            name = f"{last_name.strip()}, {first_name.strip()}"
            center = sum((w['top'] + w['bottom']) / 2 for w in row) / len(row)
            entries.append((center, name))
        return entries

    def _name_for_word(self, word, rows):
        center = (word['top'] + word['bottom']) / 2
        best = min(rows, key=lambda r: abs(r[0] - center), default=None)
        if best is None or abs(best[0] - center) > ROW_TOLERANCE:
            return None
        return best[1]

    def _enclosing_rect(self, word, rects):
        """Smallest shaded rectangle that contains the code word."""
        cx = (word['x0'] + word['x1']) / 2
        cy = (word['top'] + word['bottom']) / 2
        enclosing = [
            r for r in rects
            if r['x0'] <= cx <= r['x1'] and r['top'] <= cy <= r['bottom']
        ]
        if not enclosing:
            return None
        return min(enclosing, key=lambda r: (r['x1'] - r['x0']) * (r['bottom'] - r['top']))


def _fit_line(points):
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xx = sum(p[0] * p[0] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return 0.0, 0.0
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _round_to_five(value):
    return int(round(value / 5.0) * 5)
