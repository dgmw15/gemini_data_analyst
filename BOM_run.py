from pdf_processer import pdf_processer
from ai import material_checker

pdf_path = r"C:\Users\pauld\Downloads\Pump spare part list.pdf"

base_dir = r"C:\Users\pauld\Desktop\Output for BOM"

pdf_processor = pdf_processer(pdf_path)

doc = pdf_processor.process_pdf()
print(doc)

system_instructions_BOM = """You are an expert in organizing data extracted from bill of materials. 

The input given to you is a text version of the information extracted from a bill of material. 

Tasking: 
Please organise it and return it in JSON format. 
Return NULL should there be no information for it. 

Return the JSON output in the following format. Put information you believe for it to be under the headers. If it does not fit, do not create new columns. 
JSON example: 
[
  {
    "Part Name": "Pump",
    "Part Number": null,
    "Part Description": "AXIALLY SPLIT-CASE TWO STAGE FIRE PUMPS",
    "Equipment": null,
    "Part Category": "Fire Pump",
    "Environment 1": null,
    "Environment 2": null,
    "Conventional Material": null,
    "Manufacturer": null,
    "Manufacturer Part Number": null,
    "Weight (kg)": null,
    "Dimension X": null,
    "Dimension Y": null,
    "Dimension Z": null,
    "Price": null,
    "Price Currency": null,
  },
]
"""


try:
    output_BOM_json = material_checker.ai_api_response(doc, system_instructions_BOM)
    print(output_BOM_json)
    cleansed_BOM_output = material_checker.material_response_data_cleansed(output_BOM_json)
    dataframe_BOM = material_checker.material_response_to_dataframe(cleansed_BOM_output)
    str_output_BOM = material_checker.imposed_string_format(dataframe_BOM)
    excel_path = material_checker.get_versioned_output_path(base_dir, prefix="BOM")
    material_checker.material_response_to_excel(str_output_BOM, excel_path)
except Exception as e:
    print(f"Error: {e}")



