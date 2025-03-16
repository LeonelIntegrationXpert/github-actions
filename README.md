# GitHub Actions - MuleSoft Integration

## 🚀 Descrição do Projeto

Este projeto é uma aplicação MuleSoft projetada para demonstrações e validação da integração com GitHub Actions. Seu objetivo principal é permitir automação e execução eficiente de fluxos MuleSoft com rastreabilidade detalhada por meio de logs configurados com Log4j.

## 🔧 Tecnologias Utilizadas

- **MuleSoft Runtime 4.6.14**
- **HTTP Listener** para expor endpoints REST
- **Log4j 2** para logs detalhados e estruturados
- **MUnit** para testes automatizados
- **GitHub Actions** para automação e deploy contínuo

## 🛠️ Configuração Inicial

### 📥 Pré-requisitos

- Anypoint Studio 7.x
- Mule Runtime 4.6.14
- Java JDK 11 ou superior

### 📦 Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/github-actions-mulesoft.git
```

2. Importe o projeto no Anypoint Studio:

- Abra o Anypoint Studio
- Vá em **File → Import → Anypoint Studio Project from File System**
- Escolha a pasta clonada e importe o projeto

## ▶️ Executando o Projeto

Para executar localmente:

1. Clique com o botão direito sobre o projeto em Anypoint Studio.
2. Escolha **Run As → Mule Application**.
3. O projeto será executado localmente na porta padrão `8081`.

### 🌐 Endpoint disponível

```http
GET http://localhost:8081/test
```

### 📤 Resposta esperada

```text
It worked!
```

## 🧪 Testes Automatizados com MUnit

Este projeto inclui testes automatizados utilizando o framework **MUnit**.

- Para rodar os testes:

```bash
mvn clean test
```

### 📂 Logs dos testes

Logs detalhados serão salvos em:

```
target/munit-logs/github-actions-munit.log
```

## 📋 Estrutura do Projeto

```
.
├── src
│   ├── main
│   │   ├── mule (fluxos principais)
│   │   └── resources (configuração Log4j, propriedades, etc)
│   └── test
│       └── munit (testes automatizados)
├── pom.xml (dependências e build)
└── README.md (este documento)
```

## 📚 Documentação Oficial

- [MuleSoft Runtime Documentation](https://docs.mulesoft.com/mule-runtime/4.6/)
- [MUnit Documentation](https://docs.mulesoft.com/munit/)
- [Log4j2 Documentation](https://logging.apache.org/log4j/2.x/manual/)

## 📞 Suporte

Para dúvidas ou suporte técnico entre em contato com:

- **Leonel Dorneles Porto**
- 📧 [leoneldornelesporto@outlook.com.br](mailto:leoneldornelesporto@outlook.com.br)
- 📞 **+55 53 99180-4869**