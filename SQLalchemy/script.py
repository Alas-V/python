import os
import glob


def get_packages_from_site_packages(venv_path):
    """Получает список пакетов из Linux-структуры venv в Windows"""
    packages = []

    # Ищем папку site-packages в Linux-структуре
    site_packages_pattern = os.path.join(venv_path, "lib", "python*", "site-packages")
    site_packages_paths = glob.glob(site_packages_pattern)

    if not site_packages_paths:
        print(f"Не найдена папка site-packages по пути: {site_packages_pattern}")
        return packages

    site_packages_path = site_packages_paths[0]
    print(f"Найдена папка site-packages: {site_packages_path}")

    # Ищем все папки с .dist-info
    for item in os.listdir(site_packages_path):
        if item.endswith(".dist-info"):
            # Формат: package_name-version.dist-info
            pkg_name_with_version = item.replace(".dist-info", "")
            if "-" in pkg_name_with_version:
                # Разделяем на имя и версию
                last_dash_index = pkg_name_with_version.rfind("-")
                name = pkg_name_with_version[:last_dash_index]
                version = pkg_name_with_version[last_dash_index + 1 :]
                packages.append(f"{name}=={version}")

    return packages


# Укажите путь к вашей папке venv
venv_path = r"D:\python\SQLalchemy\venv"

try:
    packages = get_packages_from_site_packages(venv_path)

    if packages:
        # Сохраняем в requirements.txt
        with open("requirements.txt", "w", encoding="utf-8") as f:
            for package in sorted(packages):
                print(package)
                f.write(package + "\n")

        print(f"\nУспешно создан requirements.txt с {len(packages)} пакетами")
    else:
        print("Не найдено пакетов в виртуальном окружении")

except Exception as e:
    print(f"Ошибка: {e}")
    print("Проверьте правильность пути к venv")
