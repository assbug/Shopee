from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.group_system import GroupSystem


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Menu e comandos para gerenciar contatos CSV no Termux com fila de envio em ritmo controlado.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats_parser = subparsers.add_parser("stats", help="Lista grupos/canais e quantos contatos foram extraídos.")
    stats_parser.add_argument("--contacts-file", required=True, help="CSV de contatos com origem e opt-in.")

    remove_parser = subparsers.add_parser("remove", help="Marca contatos como removidos e exporta a lista simplificada.")
    remove_parser.add_argument("--contacts-file", required=True, help="CSV de contatos.")
    remove_parser.add_argument("--ids", nargs="+", required=True, help="IDs que devem ser marcados como removidos.")
    remove_parser.add_argument("--removed-file", required=True, help="CSV de saída com id, nome e sobrenome.")

    generate_parser = subparsers.add_parser("generate", help="Gera mensagens e monta a fila de envio a partir do CSV.")
    generate_parser.add_argument("--contacts-file", required=True, help="CSV de contatos.")
    generate_parser.add_argument("--messages-file", required=True, help="JSON de saída com mensagens personalizadas.")
    generate_parser.add_argument("--queue-file", required=True, help="JSON de saída com a fila de envio.")
    generate_parser.add_argument("--min-delay", type=int, default=45, help="Atraso mínimo entre envios em segundos.")
    generate_parser.add_argument("--max-delay", type=int, default=90, help="Atraso máximo entre envios em segundos.")

    send_parser = subparsers.add_parser("send", help="Processa uma fila pronta em preview, webhook ou comando local.")
    send_parser.add_argument("--queue-file", required=True, help="JSON com a fila de envio.")
    send_parser.add_argument("--sent-file", required=True, help="JSON de saída com o resultado dos envios.")
    send_parser.add_argument("--webhook-url", help="Webhook opcional para disparar cada mensagem.")
    send_parser.add_argument("--command-template", help="Comando local opcional, ex.: termux-sms-send -n {contato} {mensagem}")
    send_parser.add_argument("--execute", action="store_true", help="Executa de verdade; sem esta flag roda apenas em preview.")

    menu_parser = subparsers.add_parser("menu", help="Abre um menu interativo compatível com terminal do Termux.")
    menu_parser.add_argument("--contacts-file", required=True, help="CSV de contatos principal.")
    menu_parser.add_argument("--messages-file", default="data/mensagens_menu.json", help="Arquivo padrão para mensagens geradas.")
    menu_parser.add_argument("--queue-file", default="data/fila_menu.json", help="Arquivo padrão para fila gerada.")
    menu_parser.add_argument("--removed-file", default="data/removidos_menu.csv", help="Arquivo padrão para removidos.")
    menu_parser.add_argument("--sent-file", default="data/envios_menu.json", help="Arquivo padrão para log de envios.")
    return parser


def run_menu(system: GroupSystem, args: argparse.Namespace) -> None:
    while True:
        print("\n=== MENU TERMUX ===")
        print("1. Listar grupos/canais")
        print("2. Mostrar total extraído por origem")
        print("3. Marcar removidos por ID")
        print("4. Gerar mensagens e fila")
        print("5. Rodar preview da fila")
        print("0. Sair")
        option = input("Escolha uma opção: ").strip()

        if option == "1":
            contacts = system.load_contacts_csv(args.contacts_file)
            for item in system.summarize_sources(contacts):
                print(f"- {item['origem_tipo']}: {item['origem_nome']}")
        elif option == "2":
            contacts = system.load_contacts_csv(args.contacts_file)
            print(json.dumps(system.summarize_sources(contacts), ensure_ascii=False, indent=2))
        elif option == "3":
            ids = input("Digite os IDs separados por espaço: ").split()
            result = system.process_removal(args.contacts_file, ids, args.removed_file)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif option == "4":
            min_delay = int(input("Atraso mínimo em segundos [45]: ").strip() or "45")
            max_delay = int(input("Atraso máximo em segundos [90]: ").strip() or "90")
            result = system.process_generation(
                args.contacts_file,
                args.messages_file,
                args.queue_file,
                min_delay_seconds=min_delay,
                max_delay_seconds=max_delay,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif option == "5":
            queue = json.loads(Path(args.queue_file).read_text(encoding="utf-8"))
            result = system.dispatch_queue(queue, dry_run=True)
            system.save_json(args.sent_file, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif option == "0":
            print("Encerrando.")
            return
        else:
            print("Opção inválida.")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    system = GroupSystem()

    if args.command == "stats":
        contacts = system.load_contacts_csv(args.contacts_file)
        print(json.dumps(system.summarize_sources(contacts), ensure_ascii=False, indent=2))
    elif args.command == "remove":
        print(json.dumps(system.process_removal(args.contacts_file, args.ids, args.removed_file), ensure_ascii=False, indent=2))
    elif args.command == "generate":
        print(
            json.dumps(
                system.process_generation(
                    args.contacts_file,
                    args.messages_file,
                    args.queue_file,
                    min_delay_seconds=args.min_delay,
                    max_delay_seconds=args.max_delay,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "send":
        queue = json.loads(Path(args.queue_file).read_text(encoding="utf-8"))
        result = system.dispatch_queue(
            queue,
            webhook_url=args.webhook_url,
            command_template=args.command_template,
            dry_run=not args.execute,
        )
        system.save_json(args.sent_file, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "menu":
        run_menu(system, args)


if __name__ == "__main__":
    main()
