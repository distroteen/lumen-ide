Name:           lumen-ide
Version:        1.0.0
Release:        1%{?dist}
Summary:        Interpretador, IDE e compilador multi-linguagem com design moderno

License:        MIT
URL:            https://github.com/
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
Requires:       python3 >= 3.11
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       gtksourceview5
Recommends:     gcc
Recommends:     gcc-c++
Recommends:     nodejs

%description
Lumen IDE é um editor de código nativo para Linux (GTK4 + libadwaita)
com interface extremamente moderna inspirada no design da Apple.
Detecta automaticamente as toolchains instaladas e executa código em
Python, JavaScript, TypeScript, C, C++, Rust, Go, Java, C#, Ruby, PHP,
Lua, Perl, Bash e Kotlin, tudo rodando localmente, sem telemetria.

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install
install -Dm644 data/com.lumen.ide.desktop %{buildroot}%{_datadir}/applications/com.lumen.ide.desktop
install -Dm644 data/com.lumen.ide.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/com.lumen.ide.svg
install -Dm644 data/com.lumen.ide.appdata.xml %{buildroot}%{_datadir}/metainfo/com.lumen.ide.appdata.xml
install -Dm644 lumen/resources/com.lumen.ide.gschema.xml %{buildroot}%{_datadir}/glib-2.0/schemas/com.lumen.ide.gschema.xml

%post
glib-compile-schemas %{_datadir}/glib-2.0/schemas &> /dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
update-desktop-database %{_datadir}/applications &> /dev/null || :

%postun
glib-compile-schemas %{_datadir}/glib-2.0/schemas &> /dev/null || :
gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :
update-desktop-database %{_datadir}/applications &> /dev/null || :

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/lumen/
%{python3_sitelib}/lumen_ide-%{version}*.egg-info/
%{_bindir}/lumen-ide
%{_datadir}/applications/com.lumen.ide.desktop
%{_datadir}/icons/hicolor/scalable/apps/com.lumen.ide.svg
%{_datadir}/metainfo/com.lumen.ide.appdata.xml
%{_datadir}/glib-2.0/schemas/com.lumen.ide.gschema.xml

%changelog
* Wed Sep 16 2026 Lumen IDE Contributors <noreply@example.com> - 1.0.0-1
- Primeira versão pública do Lumen IDE.
