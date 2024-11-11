from trp import Document

class TextractParser:

    def parse(self, response):

        doc = Document(response)
        
        keys = [
            "ART/OBRA SOCIAL:",
            "PACIENTE:",
            "DOMICILIO:",
            "LOCALIDAD:",
            "PROFESIONAL:",
            "ESPECIALIDAD:",
            "No:",
            "N°:",
            "MATRICULA:"
        ]
        
        headers = [
            "FECHA",
            "HORA",
            "ENTRADA",
            "SALIDA"
        ]

        extracted_data = {
            "paciente": {
                "nombre": None,
                "obra_social": None,
                "num_obra_social": None,
                "localidad": None,
                "domicilio": None
            },
            "profesional": {
                "nombre": None,
                "especialidad": None,
                "matricula": None
            },
            "planilla": [

            ]
        }


        for page in doc.pages:
            
            for key in keys:
                field = page.form.getFieldByKey(key)
                if (field):
                    value = field.value.text if field.value is not None else None

                    match key:
                        case "PACIENTE:":
                            extracted_data["paciente"]["nombre"] = value
                        case "ART/OBRA SOCIAL:" | "ART/OBRA SOCIAL":
                            extracted_data["paciente"]["obra_social"] = value
                        case "No:" | "N°:":
                            extracted_data["paciente"]["num_obra_social"] = value
                        case "LOCALIDAD:":
                            extracted_data["paciente"]["localidad"] = value
                        case "DOMICILIO:":
                            extracted_data["paciente"]["domicilio"] = value
                        case "PROFESIONAL:":
                            extracted_data["profesional"]["nombre"] = value
                        case "MATRICULA:":
                            extracted_data["profesional"]["matricula"] = value
                        case "ESPECIALIDAD:":
                            extracted_data["profesional"]["especialidad"] = value

            for table in page.tables:
                header_cells = [cell.text.strip() for cell in table.rows[0].cells]

                header_indexes = {header: header_cells.index(header) for header in headers if header in header_cells}

                for row in table.rows[1:]:
                    row_data = {
                        "fecha": None,
                        "hora_entrada": None,
                        "hora_salida": None
                    }
                    
                    if "FECHA"  in header_indexes:
                        row_data["fecha"] = row.cells[header_indexes["FECHA"]].text.strip()
                    if "ENTRADA" in header_indexes:
                        row_data["hora_entrada"] = row.cells[header_indexes["ENTRADA"]].text.strip()
                    if "HORA" in header_indexes:
                        row_data["hora_entrada"] = row.cells[header_indexes["HORA"]].text.strip()
                    if "SALIDA" in header_indexes:
                        row_data["hora_salida"] = row.cells[header_indexes["SALIDA"]].text.strip()

                    extracted_data["planilla"].append(row_data)

        return extracted_data
