"""
language_runner.py
===================

Detecta as toolchains (compiladores/interpretadores) instaladas no
sistema e sabe como executar cada tipo de arquivo suportado.

Nenhum comando é executado com privilégios elevados. Toda execução
acontece em um subprocesso isolado, com working directory restrito
à pasta do arquivo/projeto e um timeout configurável.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Callable, Optional

# Timeout padrão (segundos) para evitar processos travados/infinitos.
DEFAULT_TIMEOUT = 30


@dataclass
class LanguageSpec:
    """Descreve como detectar e executar uma linguagem."""

    id: str
    display_name: str
    extensions: tuple[str, ...]
    # Nome do binário usado para checar disponibilidade (shutil.which)
    required_binaries: tuple[str, ...]
    # Recebe o caminho do arquivo e devolve a lista de comandos (shell) a rodar.
    build_command: Callable[[str], list[str]]
    icon_hint: str = "text-x-generic-symbolic"


def _tmp_bin(name: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"lumen_{name}")


LANGUAGES: list[LanguageSpec] = [
    LanguageSpec(
        id="python",
        display_name="Python",
        extensions=(".py", ".pyw"),
        required_binaries=("python3",),
        build_command=lambda f: ["python3", f],
        icon_hint="text-x-python-symbolic",
    ),
    LanguageSpec(
        id="javascript",
        display_name="JavaScript",
        extensions=(".js", ".mjs", ".cjs"),
        required_binaries=("node",),
        build_command=lambda f: ["node", f],
    ),
    LanguageSpec(
        id="typescript",
        display_name="TypeScript",
        extensions=(".ts", ".tsx"),
        required_binaries=("npx",),
        build_command=lambda f: ["npx", "--yes", "tsx", f],
    ),
    LanguageSpec(
        id="c",
        display_name="C",
        extensions=(".c",),
        required_binaries=("gcc",),
        build_command=lambda f: _compile_and_run(["gcc", f, "-O2", "-o", _tmp_bin("c_out")], _tmp_bin("c_out")),
    ),
    LanguageSpec(
        id="cpp",
        display_name="C++",
        extensions=(".cpp", ".cc", ".cxx", ".hpp"),
        required_binaries=("g++",),
        build_command=lambda f: _compile_and_run(["g++", f, "-O2", "-std=c++20", "-o", _tmp_bin("cpp_out")], _tmp_bin("cpp_out")),
    ),
    LanguageSpec(
        id="rust",
        display_name="Rust",
        extensions=(".rs",),
        required_binaries=("rustc",),
        build_command=lambda f: _compile_and_run(["rustc", f, "-O", "-o", _tmp_bin("rs_out")], _tmp_bin("rs_out")),
    ),
    LanguageSpec(
        id="go",
        display_name="Go",
        extensions=(".go",),
        required_binaries=("go",),
        build_command=lambda f: ["go", "run", f],
    ),
    LanguageSpec(
        id="java",
        display_name="Java",
        extensions=(".java",),
        required_binaries=("javac", "java"),
        build_command=lambda f: _compile_and_run_java(f),
    ),
    LanguageSpec(
        id="csharp",
        display_name="C#",
        extensions=(".cs",),
        required_binaries=("dotnet",),
        build_command=lambda f: ["dotnet", "run", "--project", os.path.dirname(f) or "."],
    ),
    LanguageSpec(
        id="ruby",
        display_name="Ruby",
        extensions=(".rb",),
        required_binaries=("ruby",),
        build_command=lambda f: ["ruby", f],
    ),
    LanguageSpec(
        id="php",
        display_name="PHP",
        extensions=(".php",),
        required_binaries=("php",),
        build_command=lambda f: ["php", f],
    ),
    LanguageSpec(
        id="lua",
        display_name="Lua",
        extensions=(".lua",),
        required_binaries=("lua",),
        build_command=lambda f: ["lua", f],
    ),
    LanguageSpec(
        id="perl",
        display_name="Perl",
        extensions=(".pl", ".pm"),
        required_binaries=("perl",),
        build_command=lambda f: ["perl", f],
    ),
    LanguageSpec(
        id="bash",
        display_name="Bash",
        extensions=(".sh", ".bash"),
        required_binaries=("bash",),
        build_command=lambda f: ["bash", f],
    ),
    LanguageSpec(
        id="kotlin",
        display_name="Kotlin",
        extensions=(".kts", ".kt"),
        required_binaries=("kotlinc",),
        build_command=lambda f: ["kotlinc", "-script", f] if f.endswith(".kts") else _compile_and_run_kotlin(f),
    ),
]

_EXT_INDEX: dict[str, LanguageSpec] = {}
for _lang in LANGUAGES:
    for _ext in _lang.extensions:
        _EXT_INDEX[_ext] = _lang


def _compile_and_run(compile_cmd: list[str], out_path: str) -> list[str]:
    """Gera um script de shell que compila e, se der certo, executa o binário."""
    quoted = " ".join(_shell_quote(c) for c in compile_cmd)
    return ["bash", "-lc", f"{quoted} && {_shell_quote(out_path)}"]


def _compile_and_run_java(file_path: str) -> list[str]:
    class_name = os.path.splitext(os.path.basename(file_path))[0]
    work_dir = os.path.dirname(file_path) or "."
    cmd = (
        f"javac {_shell_quote(file_path)} -d {_shell_quote(work_dir)} && "
        f"java -cp {_shell_quote(work_dir)} {_shell_quote(class_name)}"
    )
    return ["bash", "-lc", cmd]


def _compile_and_run_kotlin(file_path: str) -> list[str]:
    out = _tmp_bin("kt_out.jar")
    cmd = f"kotlinc {_shell_quote(file_path)} -include-runtime -d {_shell_quote(out)} && java -jar {_shell_quote(out)}"
    return ["bash", "-lc", cmd]


def _shell_quote(value: str) -> str:
    if not value:
        return "''"
    safe = all(c.isalnum() or c in "-_./" for c in value)
    return value if safe else "'" + value.replace("'", "'\\''") + "'"


def detect_language(file_path: str) -> Optional[LanguageSpec]:
    """Detecta a linguagem pela extensão do arquivo."""
    _, ext = os.path.splitext(file_path)
    return _EXT_INDEX.get(ext.lower())


def is_available(lang: LanguageSpec) -> bool:
    """Verifica se todos os binários necessários estão instalados."""
    return all(shutil.which(binary) is not None for binary in lang.required_binaries)


def missing_binaries(lang: LanguageSpec) -> list[str]:
    return [b for b in lang.required_binaries if shutil.which(b) is None]


def available_languages() -> list[LanguageSpec]:
    return [lang for lang in LANGUAGES if is_available(lang)]


def unavailable_languages() -> list[LanguageSpec]:
    return [lang for lang in LANGUAGES if not is_available(lang)]


@dataclass
class RunResult:
    """Resultado de uma execução, entregue de forma incremental via callbacks."""
    returncode: Optional[int] = None
    cancelled: bool = False


class LanguageRunner:
    """
    Executa um arquivo de forma assíncrona, entregando as linhas de
    stdout/stderr conforme chegam através de callbacks (thread-safe;
    quem chama deve fazer o marshalling para a thread da UI, ex. GLib.idle_add).
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False

    def run(
        self,
        file_path: str,
        on_output: Callable[[str, bool], None],
        on_finished: Callable[[RunResult], None],
    ) -> None:
        """
        on_output(line, is_stderr) é chamado para cada linha de saída.
        on_finished(result) é chamado ao terminar (ou ser cancelado).
        Deve ser chamado em uma thread separada da UI.
        """
        lang = detect_language(file_path)
        if lang is None:
            on_output(f"Nenhuma linguagem reconhecida para: {file_path}", True)
            on_finished(RunResult(returncode=-1))
            return

        if not is_available(lang):
            missing = ", ".join(missing_binaries(lang))
            on_output(
                f"Ferramentas ausentes para {lang.display_name}: {missing}. "
                f"Instale-as e tente novamente.",
                True,
            )
            on_finished(RunResult(returncode=-1))
            return

        cmd = lang.build_command(file_path)
        work_dir = os.path.dirname(file_path) or "."

        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env={**os.environ},
            )
        except OSError as exc:
            on_output(f"Falha ao iniciar o processo: {exc}", True)
            on_finished(RunResult(returncode=-1))
            return

        import threading

        def _pump(stream, is_stderr: bool):
            for line in iter(stream.readline, ""):
                if self._cancelled:
                    break
                on_output(line.rstrip("\n"), is_stderr)
            stream.close()

        t_out = threading.Thread(target=_pump, args=(self._process.stdout, False), daemon=True)
        t_err = threading.Thread(target=_pump, args=(self._process.stderr, True), daemon=True)
        t_out.start()
        t_err.start()

        try:
            returncode = self._process.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            on_output(f"Execução cancelada: tempo limite de {self.timeout}s excedido.", True)
            on_finished(RunResult(returncode=-1))
            return

        t_out.join(timeout=1)
        t_err.join(timeout=1)

        on_finished(RunResult(returncode=returncode, cancelled=self._cancelled))

    def cancel(self) -> None:
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
