from sqlalchemy import text
from app.config.database import get_session


class TestReportRepository:
    def get_or_create_report(self, panel_id):
        """Fetch existing test report for a panel or create empty ones if not exists."""
        with get_session() as session:
            # 1. Check if inspection exists
            query_insp = text('SELECT * FROM public."tbl_PanelInspection" WHERE "PanelID" = :panel_id')
            insp_result = session.execute(query_insp, {"panel_id": panel_id}).fetchone()

            if not insp_result:
                # Create inspection
                insert_insp = text('''
                    INSERT INTO public."tbl_PanelInspection" ("PanelID")
                    VALUES (:panel_id)
                    RETURNING "ID"
                ''')
                insp_id = session.execute(insert_insp, {"panel_id": panel_id}).scalar()

                # Create general inspection
                insert_gen = text('''
                    INSERT INTO public."tbl_GeneralInspection" (
                        "InspectionID", "PhysicalInspection", "PaintThickness", "PaintShade",
                        "MakeOfEquipmentAndElectricalOperation", "BillOfMaterial", "AluminumBBTorque", "Remarks"
                    )
                    VALUES (:insp_id, '-', NULL, '-', '-', '-', '-', '-')
                ''')
                session.execute(insert_gen, {"insp_id": insp_id})

                # Create IR test
                insert_ir = text('''
                    INSERT INTO public."tbl_InsulationResistance" (
                        "InspectionID",
                        "IR1_PhaseRB", "IR1_PhaseYB", "IR1_PhaseBR", "IR1_PhaseToNeutral", "IR1_PhaseToEarth", "IR1_BodyToNeutral",
                        "IR2_PhaseRB", "IR2_PhaseYB", "IR2_PhaseBR", "IR2_PhaseToNeutral", "IR2_PhaseToEarth", "IR2_BodyToNeutral",
                        "IR3_PhaseRB", "IR3_PhaseYB", "IR3_PhaseBR", "IR3_PhaseToNeutral", "IR3_PhaseToEarth", "IR3_BodyToNeutral"
                    )
                    VALUES (
                        :insp_id,
                        NULL, NULL, NULL, NULL, NULL, NULL,
                        NULL, NULL, NULL, NULL, NULL, NULL,
                        NULL, NULL, NULL, NULL, NULL, NULL
                    )
                ''')
                session.execute(insert_ir, {"insp_id": insp_id})
                
                session.commit()
                
                # Fetch again
                insp_result = session.execute(query_insp, {"panel_id": panel_id}).fetchone()

            insp_id = insp_result[0] # Assuming ID is first column or we can access by key later if mapping

            # Fetch all data
            query_gen = text('SELECT * FROM public."tbl_GeneralInspection" WHERE "InspectionID" = :insp_id')
            gen_result = session.execute(query_gen, {"insp_id": insp_id}).fetchone()

            query_ir = text('SELECT * FROM public."tbl_InsulationResistance" WHERE "InspectionID" = :insp_id')
            ir_result = session.execute(query_ir, {"insp_id": insp_id}).fetchone()

            # Convert to dict
            def row_to_dict(row, keys):
                if not row: return {}
                return dict(zip(keys, row))

            insp_keys = session.execute(query_insp, {"panel_id": panel_id}).keys()
            gen_keys = session.execute(query_gen, {"insp_id": insp_id}).keys()
            ir_keys = session.execute(query_ir, {"insp_id": insp_id}).keys()

            return {
                "inspection": row_to_dict(insp_result, insp_keys),
                "general": row_to_dict(gen_result, gen_keys),
                "ir": row_to_dict(ir_result, ir_keys)
            }

    def save_report(self, panel_id, inspection_data, general_data, ir_data):
        """Update test report data."""
        with get_session() as session:
            # 1. Get inspection ID
            query_insp = text('SELECT "ID" FROM public."tbl_PanelInspection" WHERE "PanelID" = :panel_id')
            insp_id = session.execute(query_insp, {"panel_id": panel_id}).scalar()

            if not insp_id:
                raise Exception(f"No inspection found for panel_id {panel_id}")

            # 2. Update Inspection
            update_insp = text('''
                UPDATE public."tbl_PanelInspection"
                SET "InspectorName" = :InspectorName,
                    "Remarks" = :Remarks,
                    "WitnessedBy" = :WitnessedBy,
                    "TestedBy" = :TestedBy
                WHERE "ID" = :insp_id
            ''')
            inspection_data["insp_id"] = insp_id
            session.execute(update_insp, inspection_data)

            # 3. Update General Inspection
            update_gen = text('''
                UPDATE public."tbl_GeneralInspection"
                SET "PhysicalInspection" = :PhysicalInspection,
                    "PaintThickness" = :PaintThickness,
                    "PaintShade" = :PaintShade,
                    "MakeOfEquipmentAndElectricalOperation" = :MakeOfEquipmentAndElectricalOperation,
                    "BillOfMaterial" = :BillOfMaterial,
                    "AluminumBBTorque" = :AluminumBBTorque,
                    "Remarks" = :Remarks
                WHERE "InspectionID" = :insp_id
            ''')
            general_data["insp_id"] = insp_id
            session.execute(update_gen, general_data)

            # 4. Update Insulation Resistance
            update_ir = text('''
                UPDATE public."tbl_InsulationResistance"
                SET "IR1_PhaseRB" = :IR1_PhaseRB,
                    "IR1_PhaseYB" = :IR1_PhaseYB,
                    "IR1_PhaseBR" = :IR1_PhaseBR,
                    "IR1_PhaseToNeutral" = :IR1_PhaseToNeutral,
                    "IR1_PhaseToEarth" = :IR1_PhaseToEarth,
                    "IR1_BodyToNeutral" = :IR1_BodyToNeutral,
                    
                    "IR2_PhaseRB" = :IR2_PhaseRB,
                    "IR2_PhaseYB" = :IR2_PhaseYB,
                    "IR2_PhaseBR" = :IR2_PhaseBR,
                    "IR2_PhaseToNeutral" = :IR2_PhaseToNeutral,
                    "IR2_PhaseToEarth" = :IR2_PhaseToEarth,
                    "IR2_BodyToNeutral" = :IR2_BodyToNeutral,
                    
                    "IR3_PhaseRB" = :IR3_PhaseRB,
                    "IR3_PhaseYB" = :IR3_PhaseYB,
                    "IR3_PhaseBR" = :IR3_PhaseBR,
                    "IR3_PhaseToNeutral" = :IR3_PhaseToNeutral,
                    "IR3_PhaseToEarth" = :IR3_PhaseToEarth,
                    "IR3_BodyToNeutral" = :IR3_BodyToNeutral
                WHERE "InspectionID" = :insp_id
            ''')
            ir_data["insp_id"] = insp_id
            session.execute(update_ir, ir_data)

            session.commit()
