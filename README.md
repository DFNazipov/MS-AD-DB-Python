# sender-to-db-from-ad

Предусловия:
1. Развернуть виртуальную машину, на которой развернуть службу каталогов MS Active Directory.
2. На своем хосте развернуть СУБД PostgreSQL.
3. Создать любую БД в данной СУБД. 
4. В ней создать таблицы Users, Groups и UsersInGroups.
5. Написать скрипт на языке Python, заполняющий таблицу Users в базе данных информацией о пользователях из Active Directory. Необходимые атрибуты, которые должны приходить по учетным записям MS Active Directory:

    a. GUID

    b. User Principal Name (UPN)

    c. SAMAccountname

    d. Имя

    e. Фамилия

    f. Отчество

    g. дата последнего входа в систему.

7. Также данный скрипт должен заполнять данные по группам в таблице Groups. Обязательные следующие атрибуты:

    a. GUID

    b. CN

    c. Name

7. Также скриптом должна заполняться таблица UsersInGroups. В ней должна содержаться информация в какие группы включены пользователи.
8. В рамках повторных запусков скрипта необходимо, чтобы информация во всех таблицах обновлялась
9. Необходимо продемонстрировать выполненную работу посредством добавления пользователя в ActiveDirectory, изменения их атрибутов, запуска скрипта и отображения информации в БД
В рамках запросов нужно по группе либо пользователю выводить данные и информацию по связям с группой.
В качестве результата по заданию предоставить небольшой отчет в виде листинга скрипта, скриншотов созданных таблиц и описанием действий по проверке корректной работы скрипта, то есть по пунктам 8 и 9


# Windows Server 2016 (AD)
OS: Microsoft Windows Server 2016 (with GUI)

Role: Domain Controller

Name PC: DC

Domain: innostage.test.local

IPv4: 192.168.163.24

Mask: 255.255.255.0

Gateway: 192.168.163.1

IPv6: none

Ход работы:
1. Установка ОС Microsoft Windows Server 2016 с поддержкой графического интерфейса
2. Добавление роли серева AD DS и DNS

   ![изображение](https://github.com/user-attachments/assets/b3b995af-db3f-4967-a17e-a8b3d27332ef)

3. Настройка AD DS


# PostgreSQL

Создаем базу данных, в которую будем вносить данные из AD
```
create database database_ad;
```
Создаем таблицы Users, Groups, UsersInGroups

```
CREATE TABLE Users (
    guid_user UUID PRIMARY KEY,
    upn VARCHAR(255),
    username VARCHAR(255),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_logon TIMESTAMP
);

CREATE TABLE Groups (
    guid_group UUID PRIMARY KEY,
    cn VARCHAR(255),
    group_name VARCHAR(255)
);

CREATE TABLE usersingroups_ad (
    user_guid UUID,
    group_guid UUID,
    PRIMARY KEY (user_guid, group_guid),
    FOREIGN KEY (user_guid) REFERENCES users_ad(guid_user),
    FOREIGN KEY (group_guid) REFERENCES groups_ad(guid_group)
);

```

![изображение](https://github.com/user-attachments/assets/43e721c9-0fbd-42fd-af5f-81402d4e7fb3)

