from __future__ import annotations

import csv
import json
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from random import Random
from typing import Callable, Iterable, Sequence
from urllib import request


@dataclass(frozen=True)
class Contact:
    id: str
    nome: str
    sobrenome: str
    contato: str
    origem_tipo: str
    origem_nome: str
    opt_in: bool
    removido: bool = False


class GroupSystem:
    def __init__(self, seed: int = 7) -> None:
        self._random = Random(seed)
        self._message_templates = (
            "Oi, {nome}! Tudo bem? Passei aqui porque lembrei de você com carinho e tenho um presente para te entregar. Se fizer sentido para você, me responde quando puder 💛",
            "Oi, {nome}! Espero que você esteja bem. Vim te chamar de um jeito especial porque pensei em você e separei um presente. Se quiser, eu te explico melhor com calma ✨",
            "Oi, {nome}! Como você está? Estou te mandando mensagem porque tenho um presente para você e achei melhor falar de forma bem pessoal. Se quiser conversar, eu fico por aqui 😊",
            "Oi, {nome}! Tudo certo? Lembrei de você hoje e quis te escrever com carinho: tenho um presente para você. Se fizer sentido, me responde e eu te conto os detalhes 🌷",
        )

    def load_contacts_csv(self, contacts_file: str | Path) -> list[Contact]:
        contacts_path = Path(contacts_file)
        with contacts_path.open(encoding="utf-8", newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))

        contacts = []
        for row in rows:
            contacts.append(
                Contact(
                    id=str(row["id"]).strip(),
                    nome=row["nome"].strip(),
                    sobrenome=row["sobrenome"].strip(),
                    contato=row["contato"].strip(),
                    origem_tipo=row.get("origem_tipo", "grupo").strip() or "grupo",
                    origem_nome=row.get("origem_nome", "sem_origem").strip() or "sem_origem",
                    opt_in=self._to_bool(row.get("opt_in", "false")),
                    removido=self._to_bool(row.get("removido", "false")),
                )
            )
        return contacts

    def save_contacts_csv(self, contacts_file: str | Path, contacts: Sequence[Contact]) -> None:
        contacts_path = Path(contacts_file)
        contacts_path.parent.mkdir(parents=True, exist_ok=True)
        with contacts_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["id", "nome", "sobrenome", "contato", "origem_tipo", "origem_nome", "opt_in", "removido"],
            )
            writer.writeheader()
            for contact in contacts:
                row = asdict(contact)
                row["opt_in"] = str(contact.opt_in).lower()
                row["removido"] = str(contact.removido).lower()
                writer.writerow(row)

    def remove_contacts(self, contacts: Sequence[Contact], ids_to_remove: Iterable[str]) -> tuple[list[Contact], list[Contact]]:
        ids = {str(value) for value in ids_to_remove}
        active_contacts: list[Contact] = []
        removed_contacts: list[Contact] = []
        for contact in contacts:
            if contact.id in ids:
                removed_contact = Contact(**{**asdict(contact), "removido": True})
                removed_contacts.append(removed_contact)
                active_contacts.append(removed_contact)
            else:
                active_contacts.append(contact)
        return active_contacts, removed_contacts

    def export_removed_contacts(self, removed_file: str | Path, removed_contacts: Sequence[Contact]) -> None:
        removed_path = Path(removed_file)
        removed_path.parent.mkdir(parents=True, exist_ok=True)
        with removed_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["id", "nome", "sobrenome"])
            writer.writeheader()
            for contact in removed_contacts:
                writer.writerow({"id": contact.id, "nome": contact.nome, "sobrenome": contact.sobrenome})

    def summarize_sources(self, contacts: Sequence[Contact]) -> list[dict[str, object]]:
        summary: dict[tuple[str, str], dict[str, object]] = {}
        for contact in contacts:
            key = (contact.origem_tipo, contact.origem_nome)
            item = summary.setdefault(
                key,
                {
                    "origem_tipo": contact.origem_tipo,
                    "origem_nome": contact.origem_nome,
                    "extraidos": 0,
                    "aptos_envio": 0,
                    "removidos": 0,
                },
            )
            item["extraidos"] += 1
            if contact.opt_in and not contact.removido:
                item["aptos_envio"] += 1
            if contact.removido:
                item["removidos"] += 1
        return sorted(summary.values(), key=lambda item: (str(item["origem_tipo"]), str(item["origem_nome"])))

    def create_message(self, contact: Contact) -> str:
        template = self._random.choice(self._message_templates)
        return template.format(nome=contact.nome)

    def generate_messages(self, contacts: Sequence[Contact]) -> list[dict[str, str]]:
        messages = []
        for contact in contacts:
            if not contact.opt_in or contact.removido:
                continue
            messages.append(
                {
                    "id": contact.id,
                    "nome": contact.nome,
                    "sobrenome": contact.sobrenome,
                    "contato": contact.contato,
                    "origem_tipo": contact.origem_tipo,
                    "origem_nome": contact.origem_nome,
                    "mensagem": self.create_message(contact),
                }
            )
        return messages

    def save_json(self, output_file: str | Path, payload: object) -> None:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def build_send_queue(
        self,
        messages: Sequence[dict[str, str]],
        min_delay_seconds: int = 45,
        max_delay_seconds: int = 90,
        start_time: datetime | None = None,
    ) -> list[dict[str, object]]:
        if min_delay_seconds < 5:
            raise ValueError("Use ao menos 5 segundos entre envios para respeitar limites e revisão humana.")
        if max_delay_seconds < min_delay_seconds:
            raise ValueError("max_delay_seconds deve ser maior ou igual a min_delay_seconds.")

        planned_at = start_time or datetime.now(timezone.utc)
        queue: list[dict[str, object]] = []
        for index, message in enumerate(messages):
            if index > 0:
                delay = self._random.randint(min_delay_seconds, max_delay_seconds)
                planned_at = planned_at + timedelta(seconds=delay)
            queue.append(
                {
                    **message,
                    "status": "queued",
                    "agendado_para": planned_at.isoformat(),
                }
            )
        return queue

    def dispatch_queue(
        self,
        queue: Sequence[dict[str, object]],
        webhook_url: str | None = None,
        command_template: str | None = None,
        dry_run: bool = True,
        sleeper: Callable[[float], None] | None = None,
        runner: Callable[[Sequence[str]], None] | None = None,
    ) -> list[dict[str, object]]:
        sleeper = sleeper or time.sleep
        runner = runner or self._run_command
        deliveries: list[dict[str, object]] = []
        now = datetime.now(timezone.utc)

        for item in queue:
            delivery = dict(item)
            scheduled_for = datetime.fromisoformat(str(item["agendado_para"]))
            wait_seconds = max((scheduled_for - now).total_seconds(), 0)
            delivery["espera_segundos"] = round(wait_seconds, 2)

            if not dry_run and wait_seconds > 0:
                sleeper(wait_seconds)

            if dry_run:
                delivery["status"] = "preview"
            elif command_template:
                formatted_command = command_template.format(
                    contato=item["contato"],
                    nome=item["nome"],
                    mensagem=item["mensagem"],
                )
                runner(shlex.split(formatted_command))
                delivery["status"] = "sent:command"
            elif webhook_url:
                payload = json.dumps(item, ensure_ascii=False).encode("utf-8")
                req = request.Request(
                    webhook_url,
                    data=payload,
                    headers={"Content-Type": "application/json; charset=utf-8"},
                    method="POST",
                )
                with request.urlopen(req, timeout=10) as response:
                    delivery["status"] = f"sent:webhook:{response.status}"
            else:
                delivery["status"] = "queued"

            deliveries.append(delivery)
            now = scheduled_for
        return deliveries

    def process_removal(self, contacts_file: str | Path, ids_to_remove: Iterable[str], removed_file: str | Path) -> dict[str, object]:
        contacts = self.load_contacts_csv(contacts_file)
        updated_contacts, removed_contacts = self.remove_contacts(contacts, ids_to_remove)
        self.save_contacts_csv(contacts_file, updated_contacts)
        self.export_removed_contacts(removed_file, removed_contacts)
        summary = self.summarize_sources(updated_contacts)
        return {
            "removidos": len(removed_contacts),
            "resumo": summary,
        }

    def process_generation(
        self,
        contacts_file: str | Path,
        messages_file: str | Path,
        queue_file: str | Path,
        min_delay_seconds: int = 45,
        max_delay_seconds: int = 90,
    ) -> dict[str, object]:
        contacts = self.load_contacts_csv(contacts_file)
        messages = self.generate_messages(contacts)
        queue = self.build_send_queue(messages, min_delay_seconds=min_delay_seconds, max_delay_seconds=max_delay_seconds)
        self.save_json(messages_file, messages)
        self.save_json(queue_file, queue)
        return {
            "mensagens_geradas": len(messages),
            "fila": len(queue),
        }

    def _run_command(self, command: Sequence[str]) -> None:
        subprocess.run(command, check=True)

    def _to_bool(self, value: object) -> bool:
        return str(value).strip().lower() in {"1", "true", "sim", "yes", "y"}
