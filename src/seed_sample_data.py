
# --- Imports and paths ---



from memo_db import BASE_DIR, get_connection
from concept_extractor import extract_concepts




NOTES_DIR = BASE_DIR / "sample_data" / "notes"



# --- Load note files ---



def load_note_files():
    note_files = sorted(NOTES_DIR.glob("*.txt"))
    notes = []

    for note_file in note_files:
        content = note_file.read_text(encoding = "utf-8")
        title = note_file.stem
        summary = content[:100].replace("\n", " ")

        notes.append({
            "title": title,
            "content": content,
            "summary": summary
        })
    
    return notes

    

# --- Reset Tables ---



def clear_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM note_concepts")
    cursor.execute("DELETE FROM concepts")
    cursor.execute("DELETE FROM notes")

    connection.commit()
    connection.close()   


# --- Insert Notes --- 


def insert_notes(notes):
    connection = get_connection()
    cursor = connection.cursor()

    for note in notes:
        cursor.execute(
            """
            INSERT INTO notes (title, content, summary)
            VALUES (?, ?, ?)
            """,
            (note["title"], note["content"], note["summary"])
        )

    connection.commit()
    connection.close()


def find_note_id(title):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id FROM notes
        WHERE title = ?
        """,
        (title,)
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return row[0]


# --- Fix Schema and Insert Concepts --- 


# extract_concepts input: note
# extract_concepts ouput: [{"name": "concept 이름", "type": "concept 타입"}, ...]
# concept_list = extract_concepts ouput

# extractor output -> nomalize
def normalize_concepts(concept_list):
    normalized = []
    for concept in concept_list:
        normalized.append({
            "name": concept["name"].strip().lower(),
            "type": concept["type"].strip().lower()
        })
    return normalized
    
# normalize -> insert
def insert_concept(concept):
    concept_name = concept["name"]
    concept_type = concept["type"]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id FROM concepts
        WHERE name = ? AND type = ?
        """,
        (concept_name, concept_type)
    )

    row = cursor.fetchone()

    if row is not None:
        connection.close()
        return row[0]

    cursor.execute(
        """
        INSERT INTO concepts (name, type)
        VALUES (?, ?)
        """,
        (concept_name, concept_type)
    )

    concept_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return concept_id


# note_concepts == link between notes and concepts table 
def insert_note_concepts(note_id, concept_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) FROM note_concepts
        WHERE note_id = ? AND concept_id = ?
        """,
        (note_id, concept_id)
    )

    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute(
            """
            INSERT INTO note_concepts (note_id, concept_id)
            VALUES (?, ?)
            """,
            (note_id, concept_id)
        )
    
    connection.commit()
    connection.close()


def build_note_concepts(note):
    note_id = find_note_id(note["title"])

    if note_id is None:
        print(f"error: id를 찾을 수 없음: {note['title']})")
        return

    concept_list = extract_concepts(
        note["title"],
        note["content"]
    )

    if concept_list is None:
        print(f"error: concept 추출 실패: {note['title']}")
        return

    if type(concept_list) != list:
        print (f"error: 응답이 list가 아님 : {note['title']} : {concept_list}")
        return

    normalized_concepts = normalize_concepts(concept_list)

    for concept in normalized_concepts:
        concept_id = insert_concept(concept)
        insert_note_concepts(note_id, concept_id)

    print("---concept save---")
    print("note:", note["title"])
    print("note_id: ", note_id)
    print("concepts: ", len(normalized_concepts))
    



# --- Count --- 



def count_notes():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM notes")
    count = cursor.fetchone()[0]

    connection.close()
    return count


def count_concepts():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM concepts")
    count = cursor.fetchone()[0]

    connection.close()
    return count


def count_note_concepts():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM note_concepts")
    count = cursor.fetchone()[0]

    connection.close()
    return count



# --- Execution --- 



if __name__ == "__main__":
    notes = load_note_files()

    clear_tables()
    insert_notes(notes)
    

    print("---save notes---")
    print("저장된 note수:", len(notes))
    print("누적:", count_notes())

    for note in notes:
        build_note_concepts(note)

    print("---results---")
    print("notes: ", count_notes())
    print("concepts: ", count_concepts())
    print("note_concepts: ", count_note_concepts())


