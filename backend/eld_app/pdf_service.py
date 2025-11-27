from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit


class PDFLogService:
    def __init__(self):
        self.page_size = letter
        self.margin = 0.5 * inch

    # ---------------------------------------------------------
    # UTILITIES
    # ---------------------------------------------------------
    def _draw_multiline_text(self, c, text, x, y, max_width, line_height=14, font="Helvetica", size=9):
        c.setFont(font, size)
        lines = simpleSplit(text, font, size, max_width)
        for i, line in enumerate(lines):
            c.drawString(x, y - i * line_height, line)

    # ---------------------------------------------------------
    # MAIN METHOD TO GENERATE FMCSA DAILY LOG PDF
    # ---------------------------------------------------------
    def generate_fmcsa_daily_log(self, day_data, trip_info, output_path=None):
        if output_path is None:
            output_path = f"fmcsa_log_day_{day_data['day_number']}.pdf"

        c = canvas.Canvas(output_path, pagesize=self.page_size)
        width, height = self.page_size

        # MAIN SECTIONS
        self._draw_header(c, width, height, day_data)
        self._draw_info_boxes(c, width, height, trip_info)
        self._draw_24_hour_grid(c, width, height, day_data)
        self._draw_remarks_section(c, width, height, day_data)
        self._draw_shipping_section(c, width, height)
        self._draw_recap_section(c, width, height)

        c.save()
        return output_path

    # ---------------------------------------------------------
    # SECTION 1 — HEADER (Matches the image)
    # ---------------------------------------------------------
    def _draw_header(self, c, width, height, day_data):
        top = height - 0.75 * inch
        # Format date properly
        # Normalize date into separate month/day/year strings (and a combined date_str for existing usage)
        raw_date = day_data.get("date")
        month_str = day_str = year_str = ""

        if isinstance(raw_date, str):
            s = raw_date.strip()
            # common "MM/DD/YYYY"
            if "/" in s:
                parts = s.split("/")
                if len(parts) == 3:
                    month_str, day_str, year_str = parts[0].zfill(2), parts[1].zfill(2), parts[2]
                # common "YYYY-MM-DD" or ISO
            elif "-" in s:
                try:
                    dt = datetime.fromisoformat(s)
                except Exception:
                    try:
                        dt = datetime.strptime(s, "%Y-%m-%d")
                    except Exception:
                        dt = None
            if dt:
                month_str = f"{dt.month:02d}"
                day_str = f"{dt.day:02d}"
                year_str = f"{dt.year}"
            else:
            # last resort: try parse generically
                try:
                    dt = datetime.fromisoformat(s)
                    month_str = f"{dt.month:02d}"
                    day_str = f"{dt.day:02d}"
                    year_str = f"{dt.year}"
                except Exception:
                    month_str = day_str = year_str = s
        else:
            # assume a date/datetime object
            dt = raw_date
            month_str = f"{dt.month:02d}"
            day_str = f"{dt.day:02d}"
            year_str = f"{dt.year}"
            
        def remove_parens(s):
            # safely convert to string, remove parentheses and trim whitespace
            if s is None:
                return ""
            try:
                s = str(s)
            except Exception:
                return ""
            return s.replace("(", "").replace(")", "").strip()
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(self.margin, top, "Drivers Daily Log")

        # Sub-header (24 hours)
        c.setFont("Helvetica", 8)
        c.drawString(self.margin + 0.75 * inch, top - 0.2 * inch, "[24 hours]")

        c.setFont("Helvetica", 12)
        # draw the cleaned values directly (do not re-wrap with parentheses)
        c.drawString(2.8 * inch, top , remove_parens(month_str))
        c.drawString(3.6 * inch, top , remove_parens(day_str))
        c.drawString(4.25 * inch, top , remove_parens(year_str))
        # Date boxes
        c.setFont("Helvetica", 10)
        c.drawString(2.8 * inch, top - 0.21 * inch, "(month)")
        c.drawString(3.6 * inch, top - 0.21 * inch, "(day)")
        c.drawString(4.3 * inch, top - 0.21 * inch, "(year)")

        # Lines for date
        c.line(2.7 * inch, top - 0.05 * inch, 3.3 * inch, top - 0.05 * inch)
        c.line(3.5 * inch, top - 0.05 * inch, 4.0 * inch, top - 0.05 * inch)
        c.line(4.2 * inch, top - 0.05 * inch, 4.7 * inch, top - 0.05 * inch)

        # draw slashes for date
        c.setFont("Helvetica", 12)
        c.drawString(3.4 * inch, top - 0.04 * inch, "/")
        c.drawString(4.1 * inch, top - 0.04 * inch, "/")

        # Original / duplicate text
        c.setFont("Helvetica-Bold", 8)
        c.drawString(self.margin + 4.5 * inch, top, "Original - File at home terminal.")
        c.setFont("Helvetica", 8)
        c.drawString(self.margin + 4.5 * inch, top - 0.18 * inch, "Duplicate - Driver retains this in his/her possession for 8 days.")

    # ---------------------------------------------------------
    # SECTION 2 — FROM / TO / DRIVER INFO BOXES
    # ---------------------------------------------------------
    def _draw_info_boxes(self, c, width, height, trip_info):
        y = height - 1.25 * inch

        c.setFont("Helvetica", 10)

        # FROM / TO
        c.drawString(self.margin + 0.65 * inch, y, "From:")
        c.line(self.margin + 0.64 * inch, y - 0.1 * inch, self.margin + 3.5 * inch, y - 0.1 * inch)

        c.drawString(self.margin + 4.0 * inch , y, "To:")
        c.line(self.margin + 4.0 * inch, y - 0.1 * inch, self.margin + 7.0 * inch,  y - 0.1 * inch)

        # Large row of boxes from image
        y -= 0.9 * inch
        box_height = 0.42 * inch

        # Total miles driving today
        c.drawString(self.margin + 0.50 * inch, y - 0.15 * inch, "Total Miles Driving Today")
        c.rect(self.margin + 0.35 * inch, y, 1.9 * inch, box_height)

        # Total mileage today
        c.drawString(self.margin + 2.50 * inch, y - 0.15 * inch, "Total Mileage Today")
        c.rect(self.margin + 2.35 * inch, y, 1.7 * inch, box_height)

        # Carrier
        c.drawString(self.margin + 5.0 * inch, y + 0.05 * inch, "Name of Carrier or Carriers")
        c.line(self.margin + 4.25 * inch, y + 0.2 * inch, self.margin + 7.5 * inch, y + 0.2 * inch)

        # Below row
        y -= 0.65 * inch

        c.drawString(self.margin + 0.50 * inch, y - 0.15 * inch, "Truck/Tractor and Trailer Numbers or License Plate(s)")
        c.rect(self.margin + 0.35 * inch, y, 3.7 * inch, box_height)

        c.drawString(self.margin + 5.0 * inch, y + box_height - 0.15 * inch, "Main Office Address")
        c.line(self.margin + 4.25 * inch, y + box_height, self.margin + 7.5 * inch, y + box_height)

        c.drawString(self.margin + 5.0 * inch, y - 0.15 * inch, "Home Terminal Address")
        c.line(self.margin + 4.25 * inch, y, self.margin + 7.5 * inch, y)


    # ---------------------------------------------------------
    # SECTION 3 — 24 HOUR GRID (Matches the image design)
    # ---------------------------------------------------------
    def _draw_24_hour_grid(self, c, width, height, day_data):
        grid_top = height - 3.5 * inch
        grid_left = self.margin +  0.9 * inch
        grid_width = 6.0 * inch
        row_height = 0.32 * inch
        hour_width = grid_width / 24

        # Left duty labels
        c.setFont("Helvetica", 9)
        labels = [
            "1. Off Duty",
            "2. Sleeper Berth",
            "3. Driving",
            "4. On Duty (not driving)"
        ]
        for i, text in enumerate(labels):
            self._draw_multiline_text(c, text=text, x = self.margin, y = grid_top - (i * row_height) - 0.1 * inch, max_width=0.8 * inch, line_height=11, font="Helvetica", size=9)

        # Hour numbers
        c.setFont("Helvetica", 7)
        for i in range(25):
            x = grid_left + (i * hour_width)
            c.drawCentredString(x, grid_top + 0.15 * inch, str(i))

        self._draw_multiline_text(
            c,
            text="Total Hours",
            x=grid_left + grid_width + 0.2 * inch,
            y=grid_top + 0.3 * inch,
            max_width=0.4 * inch,
            line_height=11,
            font="Helvetica",
            size=9
        )

        # Big outer grid
        c.setLineWidth(0.5)
        for h in range(25):
            x = grid_left + h * hour_width
            c.line(x, grid_top, x, grid_top - 4 * row_height)

        for r in range(5):
            y = grid_top - r * row_height
            c.line(grid_left, y, grid_left + grid_width, y)
            # horizontal line across for total hours
            c.setLineWidth(1)
            c.line(grid_left + grid_width + 0.2 * inch, y, grid_left + grid_width + 0.6 * inch, y)
            c.setLineWidth(0.5)

        # DRAW DUTY SCHEDULE LINES
        schedule = day_data.get("schedule", [])
        if schedule:
            y_map = {
                "OFF": grid_top - 0.16 * inch,
                "SB": grid_top - row_height - 0.16 * inch,
                "D": grid_top - 2 * row_height - 0.16 * inch,
                "ON": grid_top - 3 * row_height - 0.16 * inch,
            }
            c.setLineWidth(3)
            c.setStrokeColor(colors.blue)
            # first draw horizontal duty segments (thick)
            for seg in schedule:
                y = y_map.get(seg["status"], None)
                if y is not None:
                    x1 = grid_left + seg["start"] * hour_width
                    x2 = grid_left + seg["end"] * hour_width
                    c.line(x1, y, x2, y)

        
            boundaries = set()
            for seg in schedule:
                boundaries.add(grid_left + seg["start"] * hour_width)
                boundaries.add(grid_left + seg["end"] * hour_width)

            for x in sorted(boundaries):
                ys = []
                for s in schedule:
                    ys_pos = y_map.get(s["status"])
                    if ys_pos is None:
                        continue
                    sx = grid_left + s["start"] * hour_width
                    ex = grid_left + s["end"] * hour_width
                    # if this boundary touches the segment (start or end), include its y
                    if abs(sx - x) < 1e-6 or abs(ex - x) < 1e-6:
                        ys.append(ys_pos)

                if len(ys) > 1:
                    y_min = min(ys)
                    y_max = max(ys)
                    # draw vertical line connecting the changed-status lines
                    c.line(x, y_min, x, y_max)

            # restore thick width for any following duty drawing
            c.setLineWidth(3)

        c.setLineWidth(0.5)
        c.setStrokeColor(colors.black)

    # ---------------------------------------------------------
    # SECTION 4 — REMARKS
    # ---------------------------------------------------------
    def _draw_remarks_section(self, c, width, height, day_data):
        # === REMARKS TITLE ===
        y = height - 5.2 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.margin + 0.2 * inch, y, "Remarks")


        # 24-hour timeline for the remarks
        line_w = 6.0 * inch
        line_x0 = self.margin +  0.9 * inch
        line_x1 = line_x0 + line_w
        line_y = y + 0.02 * inch  

        # draw main horizontal line
        c.setLineWidth(0.8)
        c.line(line_x0, line_y, line_x1, line_y)

        # dimensions for ticks
        hour_count = 24
        hour_step = line_w / hour_count
        major_tick = 12  # points
        semi_major_tick = 8  # points
        minor_tick = 4  # points (for quarter-hours)

        c.setLineWidth(0.6)
        # draw hour ticks and labels 0..24
        c.setFont("Helvetica", 6)
        for i in range(hour_count + 1):
            x = line_x0 + i * hour_step
            # major tick
            c.line(x, line_y, x, line_y - major_tick)
            # hour label (centered above the line)
            c.drawCentredString(x, line_y + 3, str(i))

        # draw half-hour semi-major ticks
        for h in range(hour_count):
            x = line_x0 + (h + 0.5) * hour_step
            c.line(x, line_y, x, line_y - semi_major_tick)

        # draw quarter-hour minor ticks (3 per hour segment)
        for h in range(hour_count):
            for q in (1, 2, 3):
                x = line_x0 + (h + q / 4.0) * hour_step
                c.line(x, line_y, x, line_y - minor_tick)


        # # === 24-HOUR TIMELINE ===
        # line_x0 = self.margin + 0.9 * inch
        # line_x1 = line_x0 + 6.0 * inch
        # line_y = y - 0.25 * inch

        # c.setLineWidth(1.2)
        # c.line(line_x0, line_y, line_x1, line_y)

        # hour_step = 6.0 * inch / 24

        # # Hour labels: Midnight, 1, 2, ..., 11, Noon, 13, ..., 23, 24
        # c.setFont("Helvetica", 7)
        # labels = ["Midnight"] + [str(h) for h in range(1, 12)] + ["Noon"] + [str(h) for h in range(13, 24)] + ["24"]
        # for h in range(25):
        #     x = line_x0 + h * hour_step
        #     c.setLineWidth(0.8)
        #     c.line(x, line_y, x, line_y - 12)  # Major tick
        #     c.drawCentredString(x, line_y + 8, labels[h])

        # # Half-hour ticks
        # c.setLineWidth(0.6)
        # for h in range(24):
        #     x = line_x0 + (h + 0.5) * hour_step
        #     c.line(x, line_y, x, line_y - 8)

        # === REMARK WITH DIAGONAL TEXT (LIKE OFFICIAL LOG) ===
        remarks = day_data.get("schedule", [])
        # if not remarks_text:
        #     remarks_text = "Picked up Chicago, IL • Fueled Gary, IN • 30-min break • 10-hr reset St. Louis, MO • Pre-trip done"

        # Split into individual remarks
        # events = [e.strip() for e in remarks_text.replace("•", "|").replace(",", "|").split("|") if e.strip()]
        remark_types = ["OFF", "SB", "ON"]

        bar_y = line_y - 0.35 * inch

        c.setFillColorRGB(0.94, 0.94, 0.94)
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.7)

        for remark in remarks:
                y = line_y - 16
                if remark['status'] in remark_types:
                    x1 = line_x0 + remark["start"] * hour_step
                    x2 = line_x0 + remark["end"] * hour_step
                    x_center = (x1 + x2) / 2
                    # Draw line with color
                    c.setStrokeColor(colors.blue)
                    c.line(x1, y, x2, y)
                    c.line(x1, y, x1, y + minor_tick)
                    c.line(x2, y, x2, y + minor_tick)
                    # Diagonal text inside bar
                    c.saveState()
                    c.translate(x_center, bar_y)
                    c.rotate(-60)
                    c.setFont("Helvetica-Oblique", 8)
                    c.setFillColorRGB(0, 0, 0)
                    c.drawString(0, -1, remark["remark"])
                    c.restoreState()
                c.setStrokeColor(colors.black)

        # for i, event in enumerate(events):
        #     if i >= 10:  # Max 10 visible bars
        #         break
        #     ratio = (i + 0.5) / len(events) if events else 0.5
        #     x_center = line_x0 + ratio * 6.0 * inch

        #     # Draw line to show the time interval
        #     c.line(x_center, bar_y, x_center, bar_y)
        #     # Diagonal text inside bar
        #     c.saveState()
        #     c.translate(x_center, bar_y)
        #     c.rotate(-60)
        #     c.setFont("Helvetica-Oblique", 8)
        #     c.setFillColorRGB(0, 0, 0)
        #     c.drawString(0, -1, event[:28])
        #     c.restoreState()

        # Optional: city names below (uncomment if you want)
        # cities = ["Chicago", "Gary", "Indianapolis", "St. Louis", "Springfield", "Tulsa", "Oklahoma City"]
        # for i, city in enumerate(cities):
        #     x = line_x0 + (i + 0.5) * hour_step * 3.4
        #     c.setFont("Helvetica", 6.5)
        #     c.drawCentredString(x, bar_y - 0.7 * inch, city)

    # ---------------------------------------------------------
    # SECTION 5 — SHIPPING DOCUMENTS
    # ---------------------------------------------------------
    def _draw_shipping_section(self, c, width, height):
        y = height - 6.3 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.margin, y, "Shipping Documents:")

        c.setFont("Helvetica", 9)
        c.drawString(self.margin, y - 0.3 * inch, "BVL or Manifest No.: _________________________")

        c.drawString(self.margin, y - 0.6 * inch, "Shipper & Commodity")
        c.rect(self.margin, y - 1.0 * inch, 7.0 * inch, 0.7 * inch)

    # ---------------------------------------------------------
    # SECTION 6 — RECAP TABLE
    # ---------------------------------------------------------
    def _draw_recap_section(self, c, width, height):
        y = height - 7.8 * inch
        # c.setFont("Helvetica-Bold", 10)
        # c.drawString(self.margin, y, "Recap:")
        # c.setFont("Helvetica", 8)

        # # A simple 3-column recap like the image
        # c.rect(self.margin, y - 0.3 * inch, 2.2 * inch, 1.0 * inch)
        # c.rect(self.margin + 2.25 * inch, y - 0.3 * inch, 2.2 * inch, 1.0 * inch)
        # c.rect(self.margin + 4.5 * inch, y - 0.3 * inch, 2.0 * inch, 1.0 * inch)
