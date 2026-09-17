# Política de Segurança

## Modelo de segurança do Lumen IDE

- O aplicativo roda **100% localmente**. Nenhum arquivo, código ou
  telemetria é enviado para servidores externos.
- A execução de código (`Executar`) roda em um **subprocesso isolado**,
  sem privilégios elevados e sem `sudo`, usando apenas o interpretador
  ou compilador já presente no sistema do usuário.
- Toda execução tem um **timeout padrão de 30 segundos** para evitar
  processos travados ou loops infinitos consumindo recursos indefinidamente.
- O instalador (`scripts/install.sh`) só instala pacotes dos
  **repositórios oficiais** da distribuição (apt/dnf/pacman) — nunca
  baixa binários arbitrários da internet.
- Os pacotes `.deb`/`.rpm`/`PKGBUILD` não executam nenhum script com
  privilégios além do necessário para copiar arquivos e registrar o
  ícone/atalho de aplicativo.
- Recomendamos a variante **Flatpak** (`packaging/flatpak`) para quem
  quiser rodar o Lumen IDE em um sandbox ainda mais restrito.

## Reportando uma vulnerabilidade

Se você encontrar uma vulnerabilidade de segurança, por favor abra uma
issue privada (ou use o recurso de "Security Advisories" do GitHub) em
vez de divulgar publicamente antes de um patch estar disponível.
