from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.group_system import Contact, GroupSystem


class GroupSystemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.system = GroupSystem(seed=1)
        self.sample_contacts = """id,nome,sobrenome,contato,origem_tipo,origem_nome,opt_in,removido
101,Ana,Silva,+5511999999999,grupo,Ofertas VIP,true,false
102,Bruno,Souza,@bruno,canal,Novidades,false,false
103,Carla,Oliveira,+5511888888888,grupo,Ofertas VIP,true,false
104,Diego,Pereira,+5511777777777,canal,Novidades,true,true
"""

    def test_stats_and_remove_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            contacts_file = tmp_path / "contacts.csv"
            removed_file = tmp_path / "removed.csv"
            contacts_file.write_text(self.sample_contacts, encoding="utf-8")

            result = self.system.process_removal(contacts_file, ["103"], removed_file)

            self.assertEqual(result["removidos"], 1)
            summary_map = {(item["origem_tipo"], item["origem_nome"]): item for item in result["resumo"]}
            self.assertEqual(summary_map[("grupo", "Ofertas VIP")]["extraidos"], 2)
            self.assertEqual(summary_map[("grupo", "Ofertas VIP")]["removidos"], 1)
            self.assertEqual(summary_map[("canal", "Novidades")]["extraidos"], 2)

            with removed_file.open(encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows[0]["id"], "103")
            self.assertEqual(rows[0]["sobrenome"], "Oliveira")

    def test_generate_queue_only_for_opt_in_and_not_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            contacts_file = tmp_path / "contacts.csv"
            messages_file = tmp_path / "messages.json"
            queue_file = tmp_path / "queue.json"
            contacts_file.write_text(self.sample_contacts, encoding="utf-8")

            result = self.system.process_generation(
                contacts_file,
                messages_file,
                queue_file,
                min_delay_seconds=45,
                max_delay_seconds=45,
            )

            self.assertEqual(result["mensagens_geradas"], 2)
            queue = json.loads(queue_file.read_text(encoding="utf-8"))
            self.assertEqual(len(queue), 2)
            self.assertEqual(queue[0]["status"], "queued")
            self.assertIn("presente", queue[0]["mensagem"].lower())

            first_time = datetime.fromisoformat(queue[0]["agendado_para"])
            second_time = datetime.fromisoformat(queue[1]["agendado_para"])
            self.assertEqual(int((second_time - first_time).total_seconds()), 45)

    def test_dispatch_preview_does_not_send(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        queue = self.system.build_send_queue(
            [
                {
                    "id": "101",
                    "nome": "Ana",
                    "sobrenome": "Silva",
                    "contato": "+5511999999999",
                    "origem_tipo": "grupo",
                    "origem_nome": "Ofertas VIP",
                    "mensagem": "Oi, Ana! Tenho um presente para você.",
                }
            ],
            min_delay_seconds=45,
            max_delay_seconds=45,
            start_time=start,
        )

        deliveries = self.system.dispatch_queue(queue, dry_run=True)
        self.assertEqual(deliveries[0]["status"], "preview")
        self.assertIn("espera_segundos", deliveries[0])

    def test_create_message_is_humanized(self) -> None:
        contact = Contact(
            id="999",
            nome="Marina",
            sobrenome="Costa",
            contato="@marina",
            origem_tipo="grupo",
            origem_nome="Leads Premium",
            opt_in=True,
        )
        message = self.system.create_message(contact)

        self.assertIn("Marina", message)
        self.assertIn("presente", message.lower())
        self.assertTrue(message.startswith("Oi,"))


if __name__ == "__main__":
    unittest.main()
