import os
from datetime import datetime, timedelta
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class LogService:
    def __init__(self):
        self.page_size = letter
        self.margin = 0.25 * inch
        
    def generate_html_daily_log(self, day_data, trip_info):
        """Generate HTML template with data filled and lines drawn"""
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Driver's Daily Log - Day {day_data['day_number']}</title>
            <style>
                * {{
                    box-sizing: border-box;
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                }}
                body {{
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .log-container {{
                    max-width: 8.5in;
                    margin: 0 auto;
                    background-color: white;
                    padding: 0.25in;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    line-height: 1.2;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #000;
                    padding-bottom: 5px;
                }}
                .header h1 {{
                    font-size: 16px;
                    font-weight: bold;
                    margin: 5px 0;
                }}
                .header-subtitle {{
                    font-size: 10px;
                    margin: 2px 0;
                }}
                .section {{
                    margin-bottom: 15px;
                }}
                .section-title {{
                    font-weight: bold;
                    margin-bottom: 5px;
                    text-decoration: underline;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 10px;
                }}
                table, th, td {{
                    border: 1px solid #000;
                }}
                th, td {{
                    padding: 3px 5px;
                    text-align: left;
                    height: 20px;
                    vertical-align: top;
                }}
                .time-grid {{
                    display: grid;
                    grid-template-columns: repeat(10, 1fr);
                    gap: 1px;
                    margin-bottom: 10px;
                    border: 1px solid #000;
                }}
                .time-cell {{
                    border: 1px solid #000;
                    padding: 2px;
                    height: 25px;
                    text-align: center;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .grid-header-cell {{
                    font-weight: bold;
                    background-color: #f0f0f0;
                }}
                .duty-status-line {{
                    position: relative;
                    height: 20px;
                    margin: 5px 0;
                    border-bottom: 1px solid #ccc;
                }}
                .status-block {{
                    position: absolute;
                    height: 15px;
                    top: 2px;
                    background-color: #333;
                }}
                .status-off-duty {{ background-color: #4CAF50; }}
                .status-driving {{ background-color: #f44336; }}
                .status-on-duty {{ background-color: #2196F3; }}
                .status-sleeper {{ background-color: #9C27B0; }}
                .hour-marker {{
                    position: absolute;
                    top: -15px;
                    font-size: 8px;
                    color: #666;
                }}
                .remarks-box {{
                    border: 1px solid #000;
                    height: 80px;
                    padding: 5px;
                    margin-bottom: 10px;
                    white-space: pre-line;
                }}
                .shipping-box {{
                    border: 1px solid #000;
                    height: 60px;
                    padding: 5px;
                    margin-bottom: 10px;
                    white-space: pre-line;
                }}
                .data-field {{
                    padding: 2px 5px;
                    min-height: 18px;
                    border-bottom: 1px solid #999;
                }}
                .filled-data {{
                    background-color: #f9f9f9;
                    font-weight: bold;
                }}
                .print-button {{
                    background-color: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin: 10px 0;
                }}
                @media print {{
                    .print-button {{ display: none; }}
                    body {{ padding: 0; }}
                    .log-container {{ box-shadow: none; }}
                }}
            </style>
        </head>
        <body>
            <button class="print-button" onclick="window.print()">Print Log</button>
            
            <div class="log-container">
                <div class="header">
                    <h1>DRIVERS DAILY LOG</h1>
                    <div class="header-subtitle">
                        <span>[24 hours]</span>
                        <span>[{day_data.get('bream', 'bream')}]</span>
                        <span>({day_data['date'].strftime('%A')})</span>
                        <span>({day_data['date'].year})</span>
                    </div>
                    <div class="header-subtitle">
                        <span>[Origin: - {trip_info['form_data']['current_location']} at home terminal.]</span>
                    </div>
                    <div class="header-subtitle">
                        Day/trade: Driver retains its half per possession for 8 days.
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">From:</div>
                    <table>
                        <tr>
                            <th>Total Miles Driving Today</th>
                            <th>Total Mileage Today</th>
                            <th>Name of Carriers or Centers</th>
                        </tr>
                        <tr>
                            <td class="data-field filled-data">{day_data['miles_today']}</td>
                            <td class="data-field filled-data">{day_data['total_mileage']}</td>
                            <td class="data-field filled-data">{trip_info['form_data']['current_location']} Carrier</td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <div>Main Office Address</div>
                                <div class="data-field filled-data">{trip_info['form_data'].get('main_office_address', '123 Main St, Anytown, USA')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <div>Vehicle Numbers (above each unit)</div>
                                <div class="data-field filled-data">{trip_info['form_data'].get('vehicle_numbers', 'Truck: 1234, Trailer: 5678')}</div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="3">
                                <div>Home Terminal Address</div>
                                <div class="data-field filled-data">{trip_info['form_data'].get('home_terminal_address', '456 Terminal Rd, Hometown, USA')}</div>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <div class="section">
                    <div class="section-title">Duty Status</div>
                    {self._generate_duty_status_html(day_data)}
                </div>
                
                <div class="section">
                    <div class="section-title">24-Hour Grid</div>
                    {self._generate_24_hour_grid_html(day_data)}
                </div>
                
                <div class="section">
                    <div class="section-title">Remarks</div>
                    <div class="remarks-box">{self._generate_remarks_html(day_data, trip_info)}</div>
                </div>
                
                <div class="section">
                    <div class="section-title">Shipping Documents:</div>
                    <div class="shipping-box">{self._generate_shipping_docs_html(day_data, trip_info)}</div>
                </div>
                
                <div class="section">
                    <div class="section-title">Receipt Certificate set out at day</div>
                    {self._generate_receipt_certificate_html(day_data)}
                </div>
                
                <div class="section">
                    <div style="margin-top: 20px; border-top: 1px solid #000; padding-top: 10px;">
                        <div>Carrier: __________________________</div>
                        <div>Driver: __________________________</div>
                        <div style="margin-top: 5px;">Date: {day_data['date'].strftime('%m/%d/%Y')}</div>
                    </div>
                </div>
            </div>
            
            <script>
                function drawStatusLines() {{
                    const statusData = {self._get_duty_status_data(day_data)};
                    const container = document.getElementById('duty-status-container');
                    
                    statusData.forEach(status => {{
                        const lineDiv = document.createElement('div');
                        lineDiv.className = 'duty-status-line';
                        lineDiv.innerHTML = `<strong>${{status.name}}</strong>`;
                        
                        status.periods.forEach(period => {{
                            const block = document.createElement('div');
                            block.className = `status-block status-${{status.class}}`;
                            block.style.left = `${{period.start * 4.16}}%`;
                            block.style.width = `${{(period.end - period.start) * 4.16}}%`;
                            lineDiv.appendChild(block);
                        }});
                        
                        // Add hour markers
                        for (let i = 0; i <= 24; i++) {{
                            const marker = document.createElement('div');
                            marker.className = 'hour-marker';
                            marker.style.left = `${{i * 4.16}}%`;
                            marker.textContent = i === 12 ? 'Noon' : i;
                            lineDiv.appendChild(marker);
                        }}
                        
                        container.appendChild(lineDiv);
                    }});
                }}
                
                document.addEventListener('DOMContentLoaded', drawStatusLines);
            </script>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_duty_status_html(self, day_data):
        """Generate HTML for duty status checkboxes"""
        status_data = [
            {"id": "off-duty", "label": f"1.0 Off Duty ({day_data['off_duty_hours']} hrs)", "checked": day_data['off_duty_hours'] > 0},
            {"id": "sleeper", "label": f"2.5 Sleeper Berth (0 hrs)", "checked": False},
            {"id": "driving", "label": f"3.0 Driving ({day_data['driving_hours']} hrs)", "checked": day_data['driving_hours'] > 0},
            {"id": "on-duty", "label": f"4.0 On Duty ({day_data['on_duty_hours']} hrs)", "checked": day_data['on_duty_hours'] > 0}
        ]
        
        checkboxes = '\n'.join([
            f'<div style="display: inline-block; margin-right: 20px;">'
            f'<input type="checkbox" id="{s["id"]}" {"checked" if s["checked"] else ""} disabled> '
            f'<label for="{s["id"]}">{s["label"]}</label>'
            f'</div>'
            for s in status_data
        ])
        
        return f'<div>{checkboxes}</div><div id="duty-status-container" style="margin-top: 10px;"></div>'
    
    def _get_duty_status_data(self, day_data):
        """Get duty status data for JavaScript rendering"""
        return [
            {
                "name": "Off Duty",
                "class": "off-duty",
                "periods": [{"start": 0, "end": 8}, {"start": 19, "end": 24}]
            },
            {
                "name": "Driving", 
                "class": "driving",
                "periods": [{"start": 9, "end": 12}, {"start": 12.5, "end": 15.5}, {"start": 16, "end": 19}]
            },
            {
                "name": "On Duty",
                "class": "on-duty", 
                "periods": [{"start": 8, "end": 9}, {"start": 12, "end": 12.5}, {"start": 15.5, "end": 16}]
            }
        ]
    
    def _generate_24_hour_grid_html(self, day_data):
        """Generate HTML for 24-hour grid visualization"""
        hours = list(range(24))
        hour_labels = [str(h) if h != 12 else 'Noon' for h in hours]
        
        grid_html = '<div style="display: grid; grid-template-columns: 100px repeat(24, 1fr); gap: 1px; margin: 10px 0;">'
        
        # Header row
        grid_html += '<div style="font-weight: bold; background: #f0f0f0;"></div>'
        for label in hour_labels:
            grid_html += f'<div style="font-weight: bold; background: #f0f0f0; text-align: center; font-size: 10px;">{label}</div>'
        
        # Status rows
        status_rows = [
            {"name": "Off Duty", "class": "off-duty", "periods": [(0, 8), (19, 24)]},
            {"name": "Sleeper", "class": "sleeper", "periods": []},
            {"name": "Driving", "class": "driving", "periods": [(9, 12), (12.5, 15.5), (16, 19)]},
            {"name": "On Duty", "class": "on-duty", "periods": [(8, 9), (12, 12.5), (15.5, 16)]}
        ]
        
        for status in status_rows:
            grid_html += f'<div style="font-weight: bold; background: #f9f9f9;">{status["name"]}</div>'
            for hour in range(24):
                is_active = any(start <= hour < end for start, end in status["periods"])
                bg_color = {
                    "off-duty": "#4CAF50", 
                    "driving": "#f44336", 
                    "on-duty": "#2196F3",
                    "sleeper": "#9C27B0"
                }.get(status["class"], "#ffffff")
                
                color = is_active and bg_color or "transparent"
                grid_html += f'<div style="background: {color}; border: 1px solid #ddd; min-height: 20px;"></div>'
        
        grid_html += '</div>'
        return grid_html
    
    def _generate_remarks_html(self, day_data, trip_info):
        """Generate remarks content"""
        remarks = [
            f"Day {day_data['day_number']} - {day_data['date'].strftime('%m/%d/%Y')}",
            f"Driving: {day_data['driving_hours']} hrs, On Duty: {day_data['on_duty_hours']} hrs, Off Duty: {day_data['off_duty_hours']} hrs",
            f"Total Miles Today: {day_data['miles_today']}",
            f"Trip: {trip_info['form_data'].get('start_location', 'Unknown')} to {trip_info['form_data'].get('end_location', 'Unknown')}",
            "HOS Compliant - All regulations followed"
        ]
        return '\n'.join(remarks)
    
    def _generate_shipping_docs_html(self, day_data, trip_info):
        """Generate shipping documents content"""
        return f"""DV1 on Marathon No. 84

Shipper & Commodity: {trip_info['form_data'].get('commodity', 'General Freight')}
Trip from {trip_info['form_data'].get('start_location', 'N/A')} to {trip_info['form_data'].get('end_location', 'N/A')}
Use time standard of former terminal."""

    def _generate_receipt_certificate_html(self, day_data):
        """Generate receipt certificate grid"""
        headers = ["Date", "23 Hour / 5 Day", "B.", "C.", "63 Hour / 7 Day", "A.", "B.", "C.", "34", "14 year took"]
        rows = ["To stay", "Done", "to stay", "to follow", "a & b"]
        
        grid_html = '<div class="time-grid">'
        
        # Headers
        for header in headers:
            grid_html += f'<div class="time-cell grid-header-cell">{header}</div>'
        
        # Empty row
        for _ in headers:
            grid_html += '<div class="time-cell"></div>'
        
        # Data rows
        for row in rows:
            grid_html += f'<div class="time-cell">{row}</div>'
            for _ in range(9):
                grid_html += '<div class="time-cell"></div>'
        
        grid_html += '</div>'
        return grid_html

    # Keep all your existing PDF generation methods
    def generate_fmcsa_daily_log(self, day_data, trip_info, output_path=None):
        """Generate FMCSA-compliant daily log with proper grid"""
        if output_path is None:
            output_path = f"fmcsa_log_day_{day_data['day_number']}.pdf"
        
        c = canvas.Canvas(output_path, pagesize=self.page_size)
        width, height = self.page_size
        
        # Set up fonts
        c.setFont("Helvetica", 9)
        
        # Draw FMCSA header section
        self._draw_fmcsa_header(c, width, height, day_data, trip_info)
        
        # Draw the 24-hour grid
        self._draw_24_hour_grid(c, width, height, day_data)
        
        # Draw remarks and shipping info
        self._draw_bottom_sections(c, width, height, day_data)
        
        # Draw signature and certification
        self._draw_signature_section(c, width, height)
        
        c.save()
        return output_path
    
    def _draw_fmcsa_header(self, c, width, height, day_data, trip_info):
        """Draw the FMCSA header with all required information"""
        # Main title
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1 * inch, height - 0.5 * inch, "DRIVER'S DAILY LOG")
        c.setFont("Helvetica", 10)
        c.drawString(5 * inch, height - 0.5 * inch, "(ONE CALENDAR DAY - 24 HOURS)")
        
        # Original/Duplicate labels
        c.drawString(1 * inch, height - 0.7 * inch, "ORIGINAL - Submit to carrier within 13 days")
        c.drawString(4.5 * inch, height - 0.7 * inch, "DUPLICATE - Driver retains possession for eight days")
        
        # Date and miles
        c.drawString(1 * inch, height - 0.9 * inch, f"({day_data['date'].strftime('%m/%d/%Y')})")
        c.drawString(3 * inch, height - 0.9 * inch, f"(TOTAL MILES DRIVING TODAY: {day_data['miles_today']})")
        
        # Carrier information
        c.drawString(1 * inch, height - 1.1 * inch, f"({trip_info['form_data']['current_location']} TERMINAL)")
        c.drawString(4 * inch, height - 1.1 * inch, "(MAIN OFFICE ADDRESS)")
        
        # Vehicle numbers
        c.drawString(1 * inch, height - 1.3 * inch, "VEHICLE NUMBERS - (SHOW EACH UNIT)")
        
        # Certification line
        c.drawString(1 * inch, height - 1.5 * inch, "I certify that these entries are true and correct")
        c.line(4.5 * inch, height - 1.55 * inch, 7 * inch, height - 1.55 * inch)
        c.drawString(4.5 * inch, height - 1.65 * inch, "(DRIVER'S SIGNATURE IN FULL)")
        
        # Carrier name and address
        c.drawString(1 * inch, height - 1.8 * inch, f"({trip_info['form_data']['current_location']} CARRIER)")
        c.drawString(4 * inch, height - 1.8 * inch, f"({trip_info['form_data']['current_location']}, USA)")
    
    # ... Keep all your existing PDF methods (_draw_24_hour_grid, _fill_duty_status, etc.)


# Usage example:
def main():
    log_service = LogService()
    
    # Sample data
    day_data = {
        'day_number': 1,
        'date': datetime.now(),
        'miles_today': 450,
        'total_mileage': 12500,
        'driving_hours': 8.5,
        'on_duty_hours': 10.5,
        'off_duty_hours': 13.5,
        'cycle_used': 35
    }
    
    trip_info = {
        'form_data': {
            'current_location': 'Chicago',
            'main_office_address': '123 Main St, Chicago, IL',
            'home_terminal_address': '456 Terminal Rd, Chicago, IL',
            'vehicle_numbers': 'Truck: 7890, Trailer: 1234',
            'start_location': 'Chicago, IL',
            'end_location': 'St. Louis, MO',
            'commodity': 'General Freight'
        }
    }
    
    # Generate HTML
    html_content = log_service.generate_html_daily_log(day_data, trip_info)
    with open('daily_log.html', 'w') as f:
        f.write(html_content)
    
    # Generate PDF
    pdf_path = log_service.generate_fmcsa_daily_log(day_data, trip_info)
    
    print(f"HTML log saved as 'daily_log.html'")
    print(f"PDF log saved as '{pdf_path}'")

if __name__ == "__main__":
    main()