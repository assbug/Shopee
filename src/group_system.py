from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from random import Random
from typing import Iterable, Sequence
from urllib import request


@dataclass(frozen=True)
class Person:
    id: str
    nome: str
    sobrenome: str


class GroupSystem:
    def __init__(self, seed: int = 7) -> None:
        self._random = Random(seed)
        self._message_templates = (
            "Oi, {nome}! Tudo bem? Passei aqui porque lembrei de você com carinho e tenho um presente para te entregar. Se fizer sentido para você, me responde quando puder 💛",
            "Oi, {nome}! Espero que você esteja bem. Vim te chamar de um jeito especial porque pensei em você e separei um presente. Se quiser, eu te explico melhor com calma ✨",
            "Oi, {nome}! Como você está? Estou te mandando mensagem porque tenho um presente para você e achei melhor falar de forma bem pessoal. Se quiser conversar, eu fico por aqui 😊",
            "Oi, {nome}! Tudo certo? Lembrei de você hoje e quis te escrever com carinho: tenho um presente para você. Se fizer sentido, me responde e eu te conto os detalhes 🌷",
        )

    def load_group(self, group_file: str | Path) -> list[Person]:
        group_path = Path(group_file)
        data = json.loads(group_path.read_text(encoding="utf-8"))
        return [
            Person(
                id=str(item["id"]),
                nome=item["nome"].strip(),
                sobrenome=item["sobrenome"].strip(),
            )
            for item in data
        ]

    def remove_people(self, people: Sequence[Person], ids_to_remove: Iterable[str]) -> tuple[list[Person], list[Person]]:
        ids = {str(value) for value in ids_to_remove}
        removed = [person for person in people if person.id in ids]
        remaining = [person for person in people if person.id not in ids]
        return remaining, removed

    def save_group(self, group_file: str | Path, people: Sequence[Person]) -> None:
        group_path = Path(group_file)
        serialized = [asdict(person) for person in people]
        group_path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_removed_list(self, removed_file: str | Path, removed_people: Sequence[Person]) -> None:
        removed_path = Path(removed_file)
        removed_path.parent.mkdir(parents=True, exist_ok=True)

        with removed_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["id", "nome", "sobrenome"])
            writer.writeheader()
            for person in removed_people:
                writer.writerow(asdict(person))

    def create_message(self, person: Person) -> str:
        template = self._random.choice(self._message_templates)
        return template.format(nome=person.nome)

    def save_messages(self, messages_file: str | Path, removed_people: Sequence[Person]) -> list[dict[str, str]]:
        payload = []
        for person in removed_people:
            payload.append(
                {
                    "id": person.id,
                    "nome": person.nome,
                    "sobrenome": person.sobrenome,
                    "mensagem": self.create_message(person),
                }
            )

        messages_path = Path(messages_file)
        messages_path.parent.mkdir(parents=True, exist_ok=True)
        messages_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def dispatch_messages(
        self,
        messages: Sequence[dict[str, str]],
        webhook_url: str | None = None,
        sent_file: str | Path | None = None,
    ) -> list[dict[str, str]]:
        deliveries: list[dict[str, str]] = []

        for message in messages:
            delivery = {
                "id": message["id"],
                "nome": message["nome"],
                "sobrenome": message["sobrenome"],
                "mensagem": message["mensagem"],
                "status": "queued",
            }

            if webhook_url:
                payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
                req = request.Request(
                    webhook_url,
                    data=payload,
                    headers={"Content-Type": "application/json; charset=utf-8"},
                    method="POST",
                )
                with request.urlopen(req, timeout=10) as response:
                    delivery["status"] = f"sent:{response.status}"
            deliveries.append(delivery)

        if sent_file:
            sent_path = Path(sent_file)
            sent_path.parent.mkdir(parents=True, exist_ok=True)
            sent_path.write_text(json.dumps(deliveries, ensure_ascii=False, indent=2), encoding="utf-8")

        return deliveries

    def process(
        self,
        group_file: str | Path,
        ids_to_remove: Iterable[str],
        removed_file: str | Path,
        messages_file: str | Path,
        webhook_url: str | None = None,
        sent_file: str | Path | None = None,
    ) -> dict[str, object]:
        people = self.load_group(group_file)
        remaining, removed = self.remove_people(people, ids_to_remove)
        self.save_group(group_file, remaining)
        self.save_removed_list(removed_file, removed)
        messages = self.save_messages(messages_file, removed)
        deliveries = self.dispatch_messages(messages, webhook_url=webhook_url, sent_file=sent_file)
        return {
            "removidos": len(removed),
            "restantes": len(remaining),
            "mensagens": messages,
            "envios": deliveries,
        }
