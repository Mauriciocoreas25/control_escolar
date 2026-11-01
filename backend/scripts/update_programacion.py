import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from sqlalchemy import text

def run():
    db = SessionLocal()
    try:
        # 1. Normalizar nombre y codigo en row 121
        db.execute(text("UPDATE asignaturas SET nombre = 'Programacion informatica II', codigo = 'PI-II-9A' WHERE id = 121"))

        # 2. Verificar si existe seccion B
        b_exists = db.execute(text("SELECT id FROM asignaturas WHERE grado_seccion = '9° Grado - Sección B' AND nombre = 'Programacion informatica II'")).fetchone()
        if not b_exists:
            db.execute(text("INSERT INTO asignaturas (codigo, nombre, grado_seccion, profesor_nombre, descripcion) VALUES ('PI-II-9B', 'Programacion informatica II', '9° Grado - Sección B', 'Patricia Iveth Guardado', 'Informática avanzada')"))
            print("Insertada sección B para Programacion informatica II")
        else:
            print("Ya existía sección B:", b_exists)

        # 3. Materia en tabla materias
        mat = db.execute(text("SELECT id FROM materias WHERE nombre_materia = 'Programacion informatica II'")).fetchone()
        if not mat:
            db.execute(text("INSERT INTO materias (nombre_materia, descripcion) VALUES ('Programacion informatica II', 'Programación e Informática')"))
            mat_id = db.execute(text("SELECT id FROM materias WHERE nombre_materia = 'Programacion informatica II'")).fetchone()[0]
            print("Creada materia ID:", mat_id)
        else:
            mat_id = mat[0]
            print("Materia ID existente:", mat_id)

        # 4. Cargas académicas para 9A (id=17) y 9B (id=18)
        for sec_id in [17, 18]:
            c_exists = db.execute(text("SELECT id FROM cargas_academicas WHERE materia_id = :mid AND grado_seccion_id = :sid"), {"mid": mat_id, "sid": sec_id}).fetchone()
            if not c_exists:
                db.execute(text("INSERT INTO cargas_academicas (profesor_id, materia_id, grado_seccion_id) VALUES (18, :mid, :sid)"), {"mid": mat_id, "sid": sec_id})
                print(f"Vinculada carga académica para sec_id {sec_id}")

        db.commit()
        res = db.execute(text("SELECT id, codigo, nombre, grado_seccion, profesor_nombre FROM asignaturas WHERE nombre LIKE '%Programacion%'")).fetchall()
        print("Asignaturas actualizadas:", res)
    finally:
        db.close()

if __name__ == '__main__':
    run()
