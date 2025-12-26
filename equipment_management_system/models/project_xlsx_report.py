# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
# from odoo import models
#
# class ProjectWiseReport(ReportXlsx):
#     def generate_xlsx_report(self, workbook, data, projects):
#         sheet = workbook.add_worksheet("Project Wise")
#         row = 0
#
#         sheet.write(row, 0, "Project")
#         sheet.write(row, 1, "Equipment")
#         sheet.write(row, 2, "Start")
#         sheet.write(row, 3, "End")
#         sheet.write(row, 4, "Total Days")
#         row += 1
#
#         for project in projects:
#             for line in project.project_assign_equipment_ids:
#                 start = line.project_start_date
#                 end = line.project_end_date
#
#                 days = (end - start).days if start and end else 0
#
#                 sheet.write(row, 0, project.name)
#                 sheet.write(row, 1, line.equipment_id.name)
#                 sheet.write(row, 2, str(start or ""))
#                 sheet.write(row, 3, str(end or ""))
#                 sheet.write(row, 4, days)
#                 row += 1
#
#
# class EquipmentWiseReport(ReportXlsx):
#     def generate_xlsx_report(self, workbook, data, projects):
#         sheet = workbook.add_worksheet("Equipment Wise")
#         row = 0
#
#         sheet.write(row, 0, "Equipment")
#         sheet.write(row, 1, "Project")
#         sheet.write(row, 2, "Start")
#         sheet.write(row, 3, "End")
#         sheet.write(row, 4, "Total Days")
#         row += 1
#
#         for project in projects:
#             for line in project.project_assign_equipment_ids:
#                 start = line.project_start_date
#                 end = line.project_end_date
#
#                 days = (end - start).days if start and end else 0
#
#                 sheet.write(row, 0, line.equipment_id.name)
#                 sheet.write(row, 1, project.name)
#                 sheet.write(row, 2, str(start or ""))
#                 sheet.write(row, 3, str(end or ""))
#                 sheet.write(row, 4, days)
#                 row += 1

from odoo import models

class MachineryProgressXlsx(models.AbstractModel):
    _name = 'report.equipment_management_system.machinery_progress'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Machinery Progress')
        bold = workbook.add_format({'bold': True})

        # Existing headers
        base_headers = [
            'Opening Petrol',
            'Opening Diesel',
            'Closing Petrol',
            'Closing Diesel',
            'Petrol Received',
            'Diesel Received',
            'Working Hours',
            'Idle Hours',
            'Breakdown Hours',
            'Remarks'
        ]

        # New headers you want to add (change as needed)
        new_headers = [
            'Extra Column 1',
            'Extra Column 2',
            'Extra Column 3'
        ]

        # Merge both and remove duplicates (preserves order)
        final_headers = []
        for h in base_headers + new_headers:
            if h not in final_headers:
                final_headers.append(h)

        # Write headers to sheet
        row = 0
        for col, header in enumerate(final_headers):
            sheet.write(row, col, header, bold)

        # Write records
        row = 1
        for rec in records:
            col = 0
            for header in final_headers:

                # Match each header to its field
                if header == 'Opening Petrol':
                    value = rec.opening_petrol or 0.0
                elif header == 'Opening Diesel':
                    value = rec.opening_diesel or 0.0
                elif header == 'Closing Petrol':
                    value = rec.closing_petrol or 0.0
                elif header == 'Closing Diesel':
                    value = rec.closing_diesel or 0.0
                elif header == 'Petrol Received':
                    value = rec.petrol_received or 0.0
                elif header == 'Diesel Received':
                    value = rec.diesel_received or 0.0
                elif header == 'Working Hours':
                    value = rec.working_hrs or 0.0
                elif header == 'Idle Hours':
                    value = rec.idle_hrs or 0.0
                elif header == 'Breakdown Hours':
                    value = rec.breakdown_hrs or 0.0
                elif header == 'Remarks':
                    value = rec.remarks or ""

                # Your new column values
                elif header == 'Extra Column 1':
                    value = rec.id or 0   # example value
                elif header == 'Extra Column 2':
                    value = rec.create_date or ""
                elif header == 'Extra Column 3':
                    value = rec.state or ""

                else:
                    value = ""

                sheet.write(row, col, value)
                col += 1

            row += 1

