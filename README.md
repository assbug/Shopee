# Sistema de remoção de pessoas do grupo

Este projeto implementa um fluxo simples em Python para:

1. carregar participantes de um grupo a partir de um JSON;
2. remover pessoas do grupo por `id`;
3. salvar uma lista com `nome`, `sobrenome` e `id` das pessoas removidas;
4. gerar mensagens personalizadas e mais humanizadas para contato posterior;
5. opcionalmente registrar ou disparar esses envios por webhook.

## Estrutura esperada do grupo

Arquivo JSON com uma lista de objetos neste formato:

```json
[
  {
    "id": "101",
    "nome": "Ana",
    "sobrenome": "Silva"
  }
]
```

## Como usar

### Gerar lista e mensagens

```bash
python3 main.py remove \
  --group-file data/sample_group.json \
  --ids 101 103 \
  --removed-file data/removidos.csv \
  --messages-file data/mensagens.json \
  --sent-file data/envios.json
```

### Enviar para um webhook HTTP

```bash
python3 main.py remove \
  --group-file data/sample_group.json \
  --ids 101 103 \
  --removed-file data/removidos.csv \
  --messages-file data/mensagens.json \
  --sent-file data/envios.json \
  --webhook-url https://seu-endpoint.exemplo/api/messages
```

## Saídas

- `removed-file`: CSV com `id`, `nome`, `sobrenome`.
- `messages-file`: JSON com os dados da pessoa e a mensagem sugerida.
- `sent-file`: JSON com o status do envio, ficando como `queued` quando nenhum webhook é configurado.

## Exemplo de mensagem gerada

> Oi, Ana! Tudo bem? Passei aqui porque lembrei de você com carinho e tenho um presente para te entregar. Se fizer sentido para você, me responde quando puder 💛

## Testes

```bash
python3 -m unittest discover -s tests
```

## Arquivos de exemplo

- `data/sample_group.json`: base de participantes de exemplo.
- `data/exemplo_removidos.csv`: exemplo da lista gerada após remoção.
- `data/exemplo_mensagens.json`: exemplo das mensagens humanizadas geradas.
- `data/exemplo_envios.json`: exemplo do registro final de envios em fila.
