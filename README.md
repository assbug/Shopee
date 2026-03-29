# Sistema CSV para Termux com menu integrado

Este projeto foi ajustado para rodar no terminal do Termux com foco em uma operação local e auditável.

## O que o sistema faz

1. lê uma lista CSV de contatos;
2. mostra grupos e canais de origem cadastrados no CSV;
3. informa quantos contatos foram extraídos por origem;
4. marca contatos como removidos por `id` e exporta uma lista simplificada com `id`, `nome` e `sobrenome`;
5. gera mensagens em português com tom mais humanizado;
6. monta uma fila com intervalo configurável entre envios;
7. executa a fila em modo `preview`, por `webhook` ou por um comando local do Termux.

## Observação importante

O sistema só gera mensagens para contatos com `opt_in=true` no CSV. O intervalo entre envios existe para revisão, previsibilidade operacional e respeito aos limites da plataforma, não para contornar bloqueios ou políticas de terceiros.

## Formato do CSV

Use um arquivo com estes cabeçalhos:

```csv
id,nome,sobrenome,contato,origem_tipo,origem_nome,opt_in,removido
101,Ana,Silva,+5511999999999,grupo,Ofertas VIP,true,false
```

- `origem_tipo`: `grupo` ou `canal`.
- `origem_nome`: nome do grupo/canal de origem.
- `contato`: telefone, e-mail ou identificador local.
- `opt_in`: define se a pessoa autorizou receber contato.
- `removido`: impede que o contato entre novamente em fila.

## Comandos principais

### 1) Listar grupos/canais e quantos foram extraídos

```bash
python3 main.py stats --contacts-file data/contatos_exemplo.csv
```

### 2) Marcar removidos e exportar CSV simplificado

```bash
python3 main.py remove \
  --contacts-file data/contatos_exemplo.csv \
  --ids 101 104 \
  --removed-file data/removidos.csv
```

### 3) Gerar mensagens + fila segura de envio

```bash
python3 main.py generate \
  --contacts-file data/contatos_exemplo.csv \
  --messages-file data/mensagens.json \
  --queue-file data/fila.json \
  --min-delay 45 \
  --max-delay 90
```

### 4) Rodar a fila em preview

```bash
python3 main.py send \
  --queue-file data/fila.json \
  --sent-file data/envios.json
```

### 5) Rodar a fila com comando local no Termux

Exemplo genérico usando um template local:

```bash
python3 main.py send \
  --queue-file data/fila.json \
  --sent-file data/envios.json \
  --command-template 'echo Enviando para {contato}: {mensagem}' \
  --execute
```

## Menu interativo no Termux

```bash
python3 main.py menu --contacts-file data/contatos_exemplo.csv
```

O menu permite:

- listar grupos/canais;
- ver o total extraído por origem;
- marcar removidos por ID;
- gerar mensagens e fila;
- rodar preview da fila.

## Arquivos de exemplo

- `data/contatos_exemplo.csv`: contatos de exemplo para Termux.
- `data/exemplo_removidos.csv`: CSV simplificado dos removidos.
- `data/exemplo_mensagens.json`: mensagens geradas para contatos aptos.
- `data/exemplo_fila.json`: fila com horário agendado por mensagem.
- `data/exemplo_envios.json`: resultado de preview da fila.

## Testes

```bash
python3 -m unittest discover -s tests
```
