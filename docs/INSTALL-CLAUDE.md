# Instalar HydroVision no Claude

Use o pacote `claude/hydrovision-plugin.zip` gerado no build. Ele contém
`.claude-plugin/plugin.json`, `.mcp.json` e quatro skills com referências e modelos.

No Claude.ai ou Desktop, use **Personalizar / Customize → Plugins** e a opção de upload
de plugin personalizado disponível no seu workspace. Se o cliente não oferecer essa
opção, envie os quatro ZIPs individuais da pasta `claude` em **Customize → Skills →
Adicionar / Upload a skill** e conecte o MCP separadamente pelo guia do README.

Habilite criação e edição de arquivos/execução de código e as capacidades de documentos
disponíveis no cliente. A coleção não instala automaticamente essas capacidades.
Não instale os ZIPs individuais e o plugin simultaneamente, duplicando as mesmas skills.

| Conexão | Valor |
|---|---|
| Servidor | `https://simpat-mcp-prod-625238906243.us-central1.run.app/mcp` |
| Autenticação | OAuth |
| Client ID | `claude-ai` |
| Client Secret | Vazio |
| Escopo | `vision:read` |

Faça login no HydroVision com a organização desejada. Se ocorrer `invalid_client` ou
erro de redirecionamento, confira o cadastro do cliente/callback com a equipe. Não
envie a URL completa de login, tokens ou senhas. Não substitua por credenciais ChatGPT.

Comece com “Use o HydroVision para listar as empresas que posso consultar”. Depois
teste diagnóstico com fotos e um relatório com imagens no corpo/apêndice visual.
Modelos já estão incorporados; não é necessário acesso a D: pelo executor.

Instalação, OAuth e renderização real precisam ser conferidos nesta superfície. O
validador estrutural não prova que o executor consiga materializar as fotos do MCP.

Fontes: [Skills no Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude),
[Plugins no Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).
