import json
import uuid
from trp import Document

class TextractParser:
    def extract_text(self, response, extract_by="WORD"):
        line_text = []
        for block in response["Blocks"]:
            if block["BlockType"] == extract_by:
                line_text.append(block["Text"])
        return line_text

    def map_word_id(self, response):
        word_map = {}
        for block in response["Blocks"]:
            if block["BlockType"] == "WORD":
                word_map[block["Id"]] = block["Text"]
            if block["BlockType"] == "SELECTION_ELEMENT":
                word_map[block["Id"]] = block["SelectionStatus"]
        return word_map

    def extract_table_info(self, response, word_map):
        row = []
        table = {}
        ri = 0
        flag = False

        for block in response["Blocks"]:
            if block["BlockType"] == "TABLE":
                key = f"table_{uuid.uuid4().hex}"
                table_n = +1
                temp_table = []

            if block["BlockType"] == "CELL":
                if block["RowIndex"] != ri:
                    flag = True
                    row = []
                    ri = block["RowIndex"]

                if "Relationships" in block:
                    for relation in block["Relationships"]:
                        if relation["Type"] == "CHILD":
                            row.append(" ".join([word_map[i] for i in relation["Ids"]]))
                else:
                    row.append(" ")

                if flag:
                    temp_table.append(row)
                    table[key] = temp_table
                    flag = False
        return table

    def get_key_map(self, response, word_map):
        key_map = {}
        for block in response["Blocks"]:
            if block["BlockType"] == "KEY_.text_SET" and "KEY" in block["EntityTypes"]:
                for relation in block["Relationships"]:
                    if relation["Type"] == ".text":
                        value_id = relation["Ids"]
                    if relation["Type"] == "CHILD":
                        v = " ".join([word_map[i] for i in relation["Ids"]])
                        key_map[v] = value_id
        return key_map

    def get_value_map(self, response, word_map):
        value_map = {}
        for block in response["Blocks"]:
            if block["BlockType"] == "KEY_VALUE_SET" and "VALUE" in block["EntityTypes"]:
                if "Relationships" in block:
                    for relation in block["Relationships"]:
                        if relation["Type"] == "CHILD":
                            v = " ".join([word_map[i] for i in relation["Ids"]])
                            value_map[block["Id"]] = v
                else:
                    value_map[block["Id"]] = "VALUE_NOT_FOUND"

        return value_map

    def get_kv_map(self, key_map, value_map):
        final_map = {}
        for i, j in key_map.items():
            final_map[i] = "".join(["".join(value_map[k]) for k in j])
        return final_map

    def parse(self, response):
        word_map = self.map_word_id(response)
        table_info = self.extract_table_info(response, word_map)
        key_map = self.get_key_map(response, word_map)
        value_map = self.get_value_map(response, word_map)
        final_map = self.get_kv_map(key_map, value_map)

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

            # for field in page.form.fields:
            #     print("Key: {}, Value: {}".format(field.key, field.value))
            
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
