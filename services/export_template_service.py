# services/export_template_service.py
from typing import Dict, Any, List
import logging
import textwrap
import xml.etree.ElementTree as ET
from xml.dom import minidom

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExportTemplateService:
    """
    Service responsible for transforming resolved SSM standards and attributes
    into final, CAD/Data Collector compatible formats (FXL, Civil 3D Description Keys).
    """

    def __init__(self):
        logger.info("ExportTemplateService initialized.")

    def _substitute_labels(self, template: str, attributes: Dict[str, Any]) -> str:
        """
        Substitutes placeholders in the label template with actual attribute values.

        Args:
            template: Label template string with ${ATTRIBUTE} placeholders
            attributes: Dictionary of attribute key-value pairs

        Returns:
            Final label string with placeholders replaced
        """
        final_label = template
        for key, value in attributes.items():
            placeholder = f"${{{key.upper()}}}"
            final_label = final_label.replace(placeholder, str(value))

        # Clean up any unresolved placeholders
        final_label = final_label.split("$", 1)[0].strip()

        return final_label

    def generate_trimble_fxl(self, resolved_mapping: Dict[str, Any], attributes: Dict[str, Any]) -> str:
        """
        Generates a Trimble Feature eXchange Language (FXL) XML snippet.
        FXL is used for field data collectors.

        Args:
            resolved_mapping: Resolved SSM mapping containing CAD properties
            attributes: Dictionary of feature attributes including POINT_ID, FEATURE_CODE, etc.

        Returns:
            Pretty-printed XML string in FXL format
        """
        point_id = attributes.get('POINT_ID') or 999
        feature_code = attributes.get('FEATURE_CODE') or 'UNKNOWN'

        # 1. Structure the XML elements
        FXL_root = ET.Element("FXL_Feature")
        FXL_root.set("Code", str(feature_code))

        # 2. Add CAD properties as custom attributes
        ET.SubElement(FXL_root, "CAD_Layer").text = resolved_mapping.get('cad_layer') or 'C-NONE'
        ET.SubElement(FXL_root, "CAD_Block").text = resolved_mapping.get('cad_block') or 'BLOCK-NONE'

        # 3. Add Point ID and Position (Mock)
        point_data = ET.SubElement(FXL_root, "PointData")
        point_data.set("ID", str(point_id))
        ET.SubElement(point_data, "Position").text = "X=6500000.0, Y=2000000.0, Z=100.00"

        # 4. Generate the label (annotation)
        label_template = resolved_mapping.get('cad_label_style') or 'No Label Defined'
        label_text = self._substitute_labels(label_template, attributes)

        ET.SubElement(FXL_root, "Annotation").text = label_text

        # Convert to a pretty-printed string for viewing
        rough_string = ET.tostring(FXL_root, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")

        logger.info(f"Generated FXL for Point {point_id} using code {feature_code}.")
        return pretty_xml

    def generate_civil3d_desc_key(self, resolved_mapping: Dict[str, Any], attributes: Dict[str, Any]) -> str:
        """
        Generates a Civil 3D Description Key entry (text-based format).
        This defines point display and labeling rules based on the resolved feature.

        Args:
            resolved_mapping: Resolved SSM mapping containing CAD properties
            attributes: Dictionary of feature attributes including FEATURE_CODE, etc.

        Returns:
            Formatted Civil 3D Description Key entry as a string
        """
        feature_code = attributes.get('FEATURE_CODE') or 'UNKNOWN'
        cad_layer = resolved_mapping.get('cad_layer') or 'C-NONE'
        cad_block = resolved_mapping.get('cad_block') or 'BLOCK-NONE'
        cad_label_style = resolved_mapping.get('cad_label_style') or 'UTILITY-DEFAULT'
        source_mapping_id = resolved_mapping.get('source_mapping_id') or 'N/A'

        # For label preview, use the actual template if available, otherwise 'N/A'
        label_template = resolved_mapping.get('cad_label_style') or 'N/A'

        # Civil 3D uses its own Code/Layer/Style structure. This mock shows the output format.
        desc_key_entry = textwrap.dedent(f"""
        ; --- Civil 3D Description Key Entry ---
        ; Source: SSM Mapping ID {source_mapping_id}
        CODE="{feature_code}"
            LAYER="{cad_layer}"
            POINT STYLE="STANDARD"
            POINT LABEL STYLE="{cad_label_style}"
            BLOCK NAME="{cad_block}"
            TEXT HEIGHT=0.10
        ; Final Label Text (Generated Example)
        LABEL_PREVIEW="{self._substitute_labels(label_template, attributes)}"
        -------------------------------------------
        """)

        logger.info(f"Generated Civil 3D Key for code {feature_code}. Layer: {cad_layer}")
        return desc_key_entry


# --- Example Execution (for testing the service) ---
if __name__ == '__main__':
    service = ExportTemplateService()

    # 1. Mock inputs (after normalization and mapping resolution)
    mock_resolved_map = {
        "source_mapping_id": 301,
        "cad_layer": "C-SSWR-MH-48IN",
        "cad_block": "MH-48-CONC-BLOCK",
        "cad_label_style": "MH-${SIZE} / INV: ${INVERT_ELEV}"
    }

    mock_attributes = {
        "POINT_ID": 12345,
        "FEATURE_CODE": "SDMH",
        "SIZE": "48IN",
        "RIM_ELEV": 105.50,
        "INVERT_ELEV": 99.25,
        "DEPTH": 6.25,
        "MATERIAL": "CONCRETE"
    }

    print("\n--- TEST CASE 1: Trimble FXL Output ---")
    fxl_output = service.generate_trimble_fxl(mock_resolved_map, mock_attributes)
    print(fxl_output)

    print("\n--- TEST CASE 2: Civil 3D Description Key Output ---")
    c3d_output = service.generate_civil3d_desc_key(mock_resolved_map, mock_attributes)
    print(c3d_output)
