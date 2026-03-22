from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.group_system import GroupSystem, Person


class GroupSystemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.system = GroupSystem(seed=1)
        self.sample_people = [
            {"id": "101", "nome": "Ana", "sobrenome": "Silva"},
            {"id": "102", "nome": "Bruno", "sobrenome": "Souza"},
            {"id": "103", "nome": "Carla", "sobrenome": "Oliveira"},
        ]

    def test_remove_people_saves_csv_and_messages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            group_file = tmp_path / "group.json"
            removed_file = tmp_path / "removed.csv"
            messages_file = tmp_path / "messages.json"
            sent_file = tmp_path / "sent.json"
            group_file.write_text(json.dumps(self.sample_people, ensure_ascii=False), encoding="utf-8")

            result = self.system.process(
                group_file=group_file,
                ids_to_remove=["101", "103"],
                removed_file=removed_file,
                messages_file=messages_file,
                sent_file=sent_file,
            )

            self.assertEqual(result["removidos"], 2)
            self.assertEqual(result["restantes"], 1)
            self.assertEqual(result["envios"][0]["status"], "queued")

            remaining = json.loads(group_file.read_text(encoding="utf-8"))
            self.assertEqual(remaining, [{"id": "102", "nome": "Bruno", "sobrenome": "Souza"}])

            with removed_file.open(encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows[0]["nome"], "Ana")
            self.assertEqual(rows[1]["sobrenome"], "Oliveira")

            messages = json.loads(messages_file.read_text(encoding="utf-8"))
            self.assertEqual(messages[0]["id"], "101")
            self.assertIn("presente", messages[0]["mensagem"].lower())

            sent_payload = json.loads(sent_file.read_text(encoding="utf-8"))
            self.assertEqual(sent_payload[1]["status"], "queued")

    def test_create_message_is_humanized(self) -> None:
        person = Person(id="999", nome="Marina", sobrenome="Costa")
        message = self.system.create_message(person)

        self.assertIn("Marina", message)
        self.assertIn("presente", message.lower())
        self.assertTrue(message.startswith("Oi,"))


if __name__ == "__main__":
    unittest.main()
