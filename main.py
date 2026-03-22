from __future__ import annotations

import argparse
import json

from src.group_system import GroupSystem


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remove pessoas de um grupo, salva a lista e gera mensagens humanizadas.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    remove_parser = subparsers.add_parser("remove", help="Remove pessoas do grupo por id.")
    remove_parser.add_argument("--group-file", required=True, help="Arquivo JSON com os participantes do grupo.")
    remove_parser.add_argument("--ids", nargs="+", required=True, help="IDs das pessoas que devem ser removidas.")
    remove_parser.add_argument("--removed-file", required=True, help="CSV de saída com id, nome e sobrenome.")
    remove_parser.add_argument("--messages-file", required=True, help="JSON de saída com as mensagens geradas.")
    remove_parser.add_argument("--sent-file", help="JSON opcional com o registro dos envios/filas geradas.")
    remove_parser.add_argument("--webhook-url", help="Webhook opcional para disparar cada mensagem via HTTP POST.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "remove":
        system = GroupSystem()
        result = system.process(
            group_file=args.group_file,
            ids_to_remove=args.ids,
            removed_file=args.removed_file,
            messages_file=args.messages_file,
            webhook_url=args.webhook_url,
            sent_file=args.sent_file,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
