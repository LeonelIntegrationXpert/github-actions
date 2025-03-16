# MuleSoft Application - GitHub Actions Deployment
Bem-vindo(a) ao repositório oficial do projeto **github-actions**. Este projeto demonstra como automatizar builds e deploys de uma aplicação **MuleSoft** no **CloudHub 2.0**, integrando com testes MUnit, cobertura de código e pipeline via **GitHub Actions**.

---

## Sumário

1. [Descrição Geral](#descrição-geral)  
2. [Arquitetura e Fluxo Principal](#arquitetura-e-fluxo-principal)  
3. [Pré-Requisitos](#pré-requisitos)  
4. [Estrutura do Projeto](#estrutura-do-projeto)  
5. [Como Executar Localmente](#como-executar-localmente)  
6. [Testes Automatizados (MUnit)](#testes-automatizados-munit)  
7. [Pipeline GitHub Actions](#pipeline-github-actions)  
8. [Deploy no CloudHub 2.0](#deploy-no-cloudhub-20)  
9. [Configuração de Logs (Log4j2)](#configuração-de-logs-log4j2)  
10. [Contato](#contato)  
11. [Referências Oficiais](#referências-oficiais)

---

## Descrição Geral
Este repositório contém uma aplicação Mule 4 que expõe um endpoint HTTP simples, executa testes MUnit e utiliza um **pipeline GitHub Actions** para publicar artefatos no **Anypoint Exchange** e realizar deploy **automático** no **CloudHub 2.0**.

- **Runtime Mule**: 4.6.14 (canal LTS)  
- **Estratégia de Deploy**: Rolling Update  
- **Object Store V2**: Habilitado em CloudHub 2.0  
- **Logs**: Configurados com [Log4j2](log4j2.xml)  

---

## Arquitetura e Fluxo Principal
A aplicação expõe um **HTTP Listener** na rota `/test`. Quando acessado, retorna a mensagem:
```
It worked!
```
e registra logs para acompanhamento.

Exemplo de **Fluxo Principal**:
```xml
<flow name="github-actions-main-flow">
    <http:listener path="/test" config-ref="http-listener-config"/>
    <set-payload value="It worked!"/>
    <logger message="#[payload]" level="INFO"/>
</flow>
```

### Ilustração do Fluxo
![Fluxo Principal MuleSoft - Exemplo](image.png)

---

## Pré-Requisitos
- **Anypoint Studio 7.x** (ou Maven instalado para rodar via CLI)
- **Java 8** (Zulu/OpenJDK)  
- **Mule Runtime 4.6.14** (ou compatível com LTS)  
- **Conta no Anypoint Platform** com permissões em **Exchange** e **Runtime Manager** (caso vá fazer deploy)

---

## Estrutura do Projeto

```
├── src
│   ├── main
│   │   ├── mule
│   │   │   └── github-actions.xml       (Fluxo principal MuleSoft)
│   │   └── resources
│   │       ├── log4j2.xml              (Config. de logging)
│   │       ├── mule-artifact.json      (Metadados da aplicação)
│   │       └── application-types.xml   (Tipos customizados)
│   └── test
│       ├── munit
│       │   └── github-actions-suite.xml (Testes MUnit)
│       └── resources
│           └── ... (Mocks, asserts, etc.)
├── pom.xml                (Build Maven, Plugins, Deploy CloudHub 2.0)
├── build.yml              (Workflow do GitHub Actions)
├── settings.xml           (Config. Maven p/ Anypoint Exchange)
├── README.md              (Este documento)
└── ...
```

---

## Como Executar Localmente

1. **Clonar o repositório**:
   ```bash
   git clone https://github.com/seu-usuario/github-actions.git
   cd github-actions
   ```

2. **Abrir no Anypoint Studio**:  
   - File → Import → Anypoint Studio Project from File System  
   - Selecione a pasta do projeto.

3. **Rodar via Anypoint Studio**:  
   - Clique com o botão direito no projeto → Run As → Mule Application.  
   - A aplicação subirá na porta `8081`.

4. **Testar o endpoint**:
   ```bash
   curl http://localhost:8081/test
   ```
   Deve retornar:
   ```
   It worked!
   ```

---

## Testes Automatizados (MUnit)

- Este projeto possui **testes MUnit** configurados no arquivo [`github-actions-suite.xml`](github-actions-suite.xml).
- Para rodar os testes via linha de comando:
  ```bash
  mvn clean test
  ```
- Ao final, será gerado um **relatório de cobertura** no diretório:
  ```
  target/munit-reports/
  ```

### Observação
Se você ver no log:  
```
[INFO] Run of munit-maven-plugin skipped. Property [skipMunitTests] was set to true
```
Verifique se a pipeline ou o comando Maven está passando `-DskipMunitTests=true`. Remova se desejar executar de fato os testes MUnit.

---

## Pipeline GitHub Actions

Dentro do arquivo [`build.yml`](build.yml), há uma definição de workflow que:

1. **Faz checkout** do repositório  
2. **Cacheia** dependências Maven  
3. **Configura** JDK 8  
4. **Publica** a aplicação no Exchange com `mvn deploy`  
5. **Faz o deploy** no CloudHub 2.0  
   - Utiliza variáveis de ambiente (`secrets.CONNECTED_APP_CLIENT_ID` e `secrets.CONNECTED_APP_CLIENT_SECRET`) para autenticação

O pipeline é disparado automaticamente em todo **push** no branch `main`.

---

## Deploy no CloudHub 2.0

O [`pom.xml`](pom.xml) está configurado para realizar deploy no **CloudHub 2.0**. Principais destaques:

- `<muleVersion>4.6.14</muleVersion>`: runtime Mule a ser utilizado  
- `<releaseChannel>LTS</releaseChannel>`: canal de release do runtime  
- `<replicas>1</replicas>` e `<vCores>0.1</vCores>`: tamanho e número de réplicas  
- `<objectStoreV2>` habilitado em `<integrations><services>`  
- `<updateStrategy>rolling</updateStrategy>`: define o tipo de atualização

**Exemplo** de comando para forçar o deploy (via Maven local):
```bash
mvn clean deploy -DmuleDeploy \
  -Dclient.id=<CONNECTED_APP_CLIENT_ID> \
  -Dclient.secret=<CONNECTED_APP_CLIENT_SECRET>
```

> **Observação**: Caso deseje clusterizar (em `<deploymentSettings>` → `<clustered>enabled</clustered>`), lembre-se de ajustar `<replicas>` para `>= 2`.

---

## Configuração de Logs (Log4j2)

O arquivo [`log4j2.xml`](log4j2.xml) traz uma configuração **profissional** de logs:

- **Console Appender**: imprime logs no console do Anypoint Studio e CloudHub  
- **Rolling File Appender**: gera arquivos com rotação baseada em tamanho e data  
- **Log Pattern**: inclui data, nível de log, ID de correlação e caminho do processador  
- **AsyncLogger**: melhora a performance de gravação de logs

Exemplo de formato:
```
2025-03-16 10:00:00.123 [INFO ] [main] [processor: /testFlow/1] [event: 1234abcd-... ] - Mensagem de log
```

---

## Contato

Para dúvidas, suporte ou sugestões, entre em contato com:

- **Leonel Dorneles Porto**  
  - Email: [leoneldornelesporto@outlook.com.br](mailto:leoneldornelesporto@outlook.com.br)  
  - Telefone: **+55 53 99180-4869**  

---

## Referências Oficiais
- [Documentação MuleSoft 4.4](https://docs.mulesoft.com/mule-runtime/4.4/)  
- [Deploy no CloudHub 2.0](https://docs.mulesoft.com/runtime-manager/deploying-to-cloudhub-2)  
- [MUnit (Testes e Cobertura)](https://docs.mulesoft.com/munit/)  
- [Log4j2 (Manual Oficial)](https://logging.apache.org/log4j/2.x/manual/)  
- [Integração com GitHub Actions](https://docs.github.com/en/actions)

---