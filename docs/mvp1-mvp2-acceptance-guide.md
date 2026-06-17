# ERPNext 3PL MVP1/MVP2 Acceptance Guide

Документ для ручной проверки текущего состояния MVP1 и MVP2 на тестовом стенде.

> Статус: этот документ содержит старые ссылки Desk-native MVP1 и требует обновления под Desk-native MVP1 flow. Для актуальных технических имен, URL и ролей использовать `docs/operational-names.md`; для клиентского входа использовать `/desk/3pl-client`.

Цель: быстро пройти основные клиентские и складские процессы, понять что уже реализовано, где это находится, и какой результат считается корректным.

## Доступы

Основной адрес стенда:

<https://erpnext.77.237.244.169.sslip.io>

Пароли не хранятся в репозитории. Использовать значения из серверного `.env`.

| Роль | Логин | Пароль | Назначение |
| --- | --- | --- | --- |
| Клиент | `alpha.client@example.test` | `CLIENT_DESK_PASSWORD` | Клиентский Desk, клиент `Demo Client Alpha` |
| Warehouse Operator | `warehouse.demo@example.test` | `WAREHOUSE_OPERATOR_PASSWORD` | Операционные складские действия |
| Warehouse Manager | `warehouse.manager@example.test` | `WAREHOUSE_MANAGER_PASSWORD` | Складские действия + review очереди |
| Business Owner | `BUSINESS_OWNER_USER` | `BUSINESS_OWNER_PASSWORD` | Владелец/администратор системы |
| Administrator | `Administrator` | `ADMIN_PASSWORD` | Полный системный администратор |

## Быстрые Ссылки

### Клиентский Desk

| Раздел | Полная ссылка | Что проверять |
| --- | --- | --- |
| Receiving Notices | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | список входящих заявок клиента |
| New Receiving Notice | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | создание заявки на завоз товара |
| Products | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | карточки товаров клиента |
| Product Export | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | выгрузка товаров; bulk import остается roadmap/post-MVP1 |
| Inventory | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | текущие остатки клиента |
| Shipment Requests | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | заявки клиента на отгрузку |
| New Shipment Request | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | создание заявки на отгрузку |
| Shipment Tracking | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | статусы отгрузок |
| Discrepancies | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | расхождения по приемке |
| Discrepancy Instructions | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> | инструкции клиента по расхождениям |

### Складские страницы

| Раздел | Полная ссылка | Что проверять |
| --- | --- | --- |
| Warehouse Workspace | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-warehouse> | рабочее место склада |
| Receiving | <https://erpnext.77.237.244.169.sslip.io/warehouse/receiving> | приемка товара в temporary receiving |
| Receiving Review | <https://erpnext.77.237.244.169.sslip.io/warehouse/receiving-review> | сверка и review входящих заявок |
| Putaway | <https://erpnext.77.237.244.169.sslip.io/warehouse/putaway> | размещение коробки/контейнера в storage |
| Container Move | <https://erpnext.77.237.244.169.sslip.io/warehouse/container-move> | перемещение между локациями |
| Container Repack | <https://erpnext.77.237.244.169.sslip.io/warehouse/repack> | переукомплектовка коробок/контейнеров |
| Correction | <https://erpnext.77.237.244.169.sslip.io/warehouse/correction> | складская корректировка количества/состояния |
| Correction Review | <https://erpnext.77.237.244.169.sslip.io/warehouse/correction-review> | review неоднозначных корректировок |
| Stocktake | <https://erpnext.77.237.244.169.sslip.io/warehouse/stocktake> | инвентаризация |
| Picking Confirmation | <https://erpnext.77.237.244.169.sslip.io/warehouse/picking-confirmation> | подтверждение picking |
| Outbound Fulfillment | <https://erpnext.77.237.244.169.sslip.io/warehouse/outbound-fulfillment> | packing и shipping |

## Что Проверять В Первую Очередь

1. Клиент не попадает в ERPNext Desk и работает через портал.
2. Клиент видит только данные своего клиента `Demo Client Alpha`.
3. Клиент может вести свои товары.
4. Клиент может создать Receiving Notice с выбором товаров из своего каталога.
5. Клиент может создать Shipment Request с выбором товаров из своего каталога.
6. Склад может принять товар в `Temporary Receiving - 3`.
7. Склад может сравнить ожидаемое и фактическое количество.
8. Склад может перемещать коробки/контейнеры по локациям.
9. Склад может выполнить picking/packing/shipping по клиентской заявке.
10. Склад может делать corrections и stocktake.
11. Отчеты показывают остатки и оборот операций.

## Ключевая Модель

### Клиентские Товары

Клиент управляет товарами через портал:

<https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>

Бизнес-уникальность товара:

`Client + Client SKU`

ERPNext `Item` остается системной складской карточкой. Клиент работает с `Three PL Client Product`, а синхронизация создает/обновляет ERPNext `Item`.

Клиент может:

- создать товар;
- обновить товар;
- добавить описание, UOM, barcode, фото;
- деактивировать товар вместо удаления;
- экспортировать товары CSV.

### Клиентские Заявки

Receiving Notice и Shipment Request больше не должны быть просто текстовым описанием товаров.

В клиентском портале товары выбираются из активных синхронизированных карточек клиента через поиск по SKU/названию. Система затем разворачивает выбранные строки в child tables:

- `Inbound Shipment Notice Item`;
- `Three PL Shipment Request Item`.

Служебное поле `portal_items_description` оставлено для совместимости и хранения structured JSON.

## Клиентский Портал

Стартовые ссылки клиента:

- Receiving Notices: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>
- Products: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>
- Product Export: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>
- Inventory: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>
- Shipment Requests: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>
- Shipment Tracking: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>
- Discrepancies: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>
- Discrepancy Instructions: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>

Ожидание:

- клиент остается в portal UI;
- нет `Not permitted`;
- нет `Page not found`;
- нет перехода в ERPNext Desk;
- меню портала доступно на всех страницах.

## MVP2. Product Management

### TC-P01: Клиент Создает Товар

Роль: клиент.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Создать новый product.
3. Заполнить:
   - Client SKU;
   - Product Name;
   - UOM;
   - Description;
   - Barcode, если есть;
   - Photo, если нужно;
   - Status = `Active`.
4. Сохранить.

Ожидаемый результат:

- товар появляется в списке клиента;
- клиент не выбирает Customer вручную;
- товар относится к `Demo Client Alpha`;
- после sync создается/обновляется ERPNext `Item`;
- в `Three PL Client Product Change Log` появляется запись.

### TC-P02: Клиент Обновляет Товар

Роль: клиент.

Шаги:

1. Открыть существующий товар.
2. Изменить название/описание/barcode.
3. Сохранить.

Ожидаемый результат:

- изменения сохраняются;
- ERPNext `Item` обновляется после sync;
- изменение попадает в change log.

### TC-P03: Клиент Деактивирует Товар

Роль: клиент.

Шаги:

1. Открыть товар.
2. Установить `Status = Inactive`.
3. Сохранить.

Ожидаемый результат:

- товар не удаляется физически;
- связанный ERPNext `Item` получает `disabled = 1`;
- история товара сохраняется.

### TC-P04: Импорт Товаров

Роль: клиент.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Скачать template CSV.
3. Заполнить строки:
   - `client_sku`;
   - `product_name`;
   - `product_description`;
   - `uom`;
   - `barcode`;
   - `product_image`;
   - `status`;
   - `notes`.
4. При необходимости открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> и скачать текущий список товаров.

Ожидаемый результат:

- товар создается/обновляется в `Three PL Client Product`;
- товар синхронизируется в ERPNext `Item`;
- клиент может выгрузить текущий список товаров;
- bulk Product Import не входит в MVP1 и остается post-MVP1 roadmap.

### TC-P05: Экспорт Товаров

Роль: клиент.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Нажать `Download Products CSV`.

Ожидаемый результат:

- скачивается CSV со своими товарами клиента;
- товары другого клиента не попадают в экспорт.

## MVP1. Receiving Flow

### TC-R01: Клиент Создает Receiving Notice

Роль: клиент.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Проверить, что `Client Notice Ref` предзаполнен в формате `ALPHA-IN-YYYYMMDD-###`.
3. Указать `Expected Arrival Date`.
4. В блоке `Products and Quantities` найти товар по SKU или названию.
5. Выбрать товар, указать expected qty, добавить строку.
6. Добавить notes, если нужно.
7. Сохранить.

Ожидаемый результат:

- клиент не выбирает Customer вручную;
- товары выбираются из каталога клиента;
- создается `Inbound Shipment Notice`;
- в документе есть строки `Inbound Shipment Notice Item`;
- ref сохраняется в `external_reference`;
- клиент видит notice в своем списке.

### TC-R02: Склад Принимает Товар

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/receiving>.
2. Указать Receiving Notice / ASN.
3. Указать Container / Box, например новый или demo container.
4. Указать Item.
5. Указать qty.
6. Указать receiving location: `Temporary Receiving - 3`.
7. Указать condition: `OK`, `Damaged`, `Quality Issue` или `Hold`.
8. Submit receipt.

Ожидаемый результат:

- создается submitted Stock Entry типа `3PL Inbound Receipt`;
- Stock Entry связан с client, receiving notice, container, location;
- container получает/обновляет содержимое;
- создается movement history `Received`;
- Receiving Notice получает received qty / variance qty.

### TC-R03: Сравнение Expected vs Actual

Роль: Warehouse Manager.

Шаги:

1. Открыть `Inbound Shipment Notice`.
2. Найти notice, по которому была приемка.
3. Проверить rows:
   - expected qty;
   - received qty;
   - variance qty.
4. Проверить `Discrepancies`.

Ожидаемый результат:

- если количество совпало, variance = 0;
- если есть расхождение, создается discrepancy;
- поддерживаются missing, unexpected, quantity difference, damaged, quality issue.

### TC-R04: Клиент Смотрит Discrepancies

Роль: клиент.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Найти discrepancy по своему notice.
3. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
4. Создать instruction для warehouse.

Ожидаемый результат:

- клиент видит только свои discrepancies;
- клиент может отправить инструкцию;
- инструкция сохраняется как `Three PL Client Instruction`.

## MVP1. Putaway And Location Movement

### TC-L01: Putaway Из Receiving В Storage

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/putaway>.
2. Указать container/box.
3. Указать source location, например `Temporary Receiving - 3`.
4. Указать target storage location.
5. Submit.

Ожидаемый результат:

- container меняет текущую location;
- создается `Three PL Container Movement` с type `Putaway`;
- товар не размещается напрямую в storage до receiving/verification этапа.

### TC-L02: Перемещение Между Локациями

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/container-move>.
2. Указать container.
3. Указать from/to warehouse locations.
4. Submit move.

Ожидаемый результат:

- current warehouse у container обновляется;
- создается movement history;
- inventory snapshots после sync отражают новую location.

## MVP1. Shipment / Picking / Dispatch Flow

### TC-S01: Клиент Создает Shipment Request

Роль: клиент.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Проверить, что `Client Shipment Ref` предзаполнен в формате `ALPHA-OUT-YYYYMMDD-###`.
3. Указать requested ship date.
4. Указать destination name/address.
5. Найти товар через поиск по SKU/названию.
6. Добавить qty.
7. Сохранить.

Ожидаемый результат:

- создается `Three PL Shipment Request`;
- строки товаров создаются как `Three PL Shipment Request Item`;
- клиент не выбирает Customer вручную;
- ref сохраняется в `external_reference`;
- клиент видит request в списке.

### TC-S02: Система Создает Pick List

Роль: Warehouse Manager.

Шаги:

1. Дождаться sync или запустить post-deploy/sync процесс.
2. Открыть `Pick List`.
3. Найти Pick List по shipment reference.

Ожидаемый результат:

- Pick List создан из Shipment Request;
- содержит client;
- содержит shipment request;
- содержит shipment reference;
- строки аллоцированы из available inventory snapshots;
- связанные containers получают status `Picking`.

### TC-S03: Picking Confirmation

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/picking-confirmation>.
2. Указать Pick List.
3. Указать container.
4. Confirm picked.

Ожидаемый результат:

- picked qty обновляется;
- container получает status `Picked`;
- создается movement history `Picking`/`Picked`.

### TC-S04: Packing / Shipping

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/outbound-fulfillment>.
2. Указать shipment request / reference.
3. Указать container.
4. Выполнить packing или shipping step.

Ожидаемый результат:

- создается/обновляется Stock Entry для packing/shipping;
- shipment request получает актуальный status;
- container movement history обновляется;
- клиент видит status в <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.

## MVP1. Corrections

### TC-C01: Quantity Correction

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/correction>.
2. Указать container/location/item.
3. Указать counted/actual qty.
4. Submit correction.

Ожидаемый результат:

- создается `Three PL Warehouse Correction`;
- container contents обновляются;
- movement history получает `Adjusted`;
- если delta однозначная, создается ERPNext Stock Entry `3PL Quantity Gain` или `3PL Quantity Loss`;
- если correction неоднозначная, она уходит в `Needs Review`.

### TC-C02: Correction Review

Роль: Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/correction-review>.
2. Найти correction со статусом `Needs Review`.
3. Принять решение и добавить notes.

Ожидаемый результат:

- correction получает review decision;
- сохраняется reviewer и timestamp;
- correction больше не висит как новая необработанная проблема.

## MVP1. Stocktake

### TC-ST01: Stocktake By Container / SKU

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/warehouse/stocktake>.
2. Выбрать stocktake session или создать новую.
3. Указать location/container/item.
4. Указать counted qty.
5. Submit.

Ожидаемый результат:

- создается `Three PL Stocktake`;
- фиксируется counted qty и system qty;
- если есть delta, создается linked correction;
- stocktake виден в reports.

## Reports

### TC-REP01: Client Inventory

Роль: клиент.

Шаги:

1. Открыть <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Проверить товары клиента.

Ожидаемый результат:

- видны только Alpha products;
- Beta products не видны.

### TC-REP02: Product Balance On Date

Роль: Warehouse Manager или Business Owner.

Шаги:

1. Открыть report `3PL Inventory Balance By Date`.
2. Выбрать client/date.
3. Проверить rows.

Ожидаемый результат:

- отчет показывает balance snapshot на дату;
- история доступна с момента генерации snapshots.

### TC-REP03: Warehouse Operation Turnover

Роль: Warehouse Manager или Business Owner.

Шаги:

1. Открыть report `3PL Warehouse Operation Turnover`.
2. Выбрать период.
3. Проверить движения.

Ожидаемый результат:

- видны receiving, putaway, moves, corrections, stocktake, picking, packing/shipping движения;
- можно отфильтровать по client / warehouse / period.

## Data Isolation Checks

### TC-SEC01: Alpha Client Does Not See Beta Data

Роль: клиент `alpha.client@example.test`.

Шаги:

1. Открыть клиентский Inventory: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
2. Открыть Receiving Notices: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
3. Открыть Shipment Requests: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
4. Открыть Products: <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client>.
5. Попробовать найти `Demo Client Beta`, `SKU-BETA-001`, `ASN-BETA-001`.

Ожидаемый результат:

- Beta данные не видны;
- клиент не может создать запись для другого Customer;
- нет скрытых ошибок `Not permitted` на страницах, которые доступны из меню.

## Smoke Checks После Любых Изменений

Перед передачей заказчику полезно открыть эти страницы в браузере:

| # | Для кого | Что открыть | Полная ссылка |
| --- | --- | --- | --- |
| 1 | Клиент | Receiving Notices | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 2 | Клиент | New Receiving Notice | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 3 | Клиент | Products | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 4 | Клиент | Product Export | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 5 | Клиент | Inventory | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 6 | Клиент | Shipment Requests | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 7 | Клиент | New Shipment Request | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 9 | Клиент | Discrepancies | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 10 | Клиент | Discrepancy Instructions | <https://erpnext.77.237.244.169.sslip.io/desk/3pl-client> |
| 11 | Склад | Receiving | <https://erpnext.77.237.244.169.sslip.io/warehouse/receiving> |
| 12 | Склад | Putaway | <https://erpnext.77.237.244.169.sslip.io/warehouse/putaway> |
| 13 | Склад | Container Move | <https://erpnext.77.237.244.169.sslip.io/warehouse/container-move> |
| 14 | Склад | Correction | <https://erpnext.77.237.244.169.sslip.io/warehouse/correction> |
| 15 | Склад | Stocktake | <https://erpnext.77.237.244.169.sslip.io/warehouse/stocktake> |
| 16 | Склад | Picking Confirmation | <https://erpnext.77.237.244.169.sslip.io/warehouse/picking-confirmation> |
| 17 | Склад | Outbound Fulfillment | <https://erpnext.77.237.244.169.sslip.io/warehouse/outbound-fulfillment> |

Ожидаемый результат:

- страницы открываются;
- нет `Page not found`;
- нет `Not permitted`;
- клиентские страницы не требуют повторного логина в одной сессии;
- клиент не попадает в Desk;
- warehouse users попадают в warehouse workspace.

## Что Еще Не Является Финально Полированным

Текущая система готова для MVP-проверки, но не является финальной production-polished версией.

Оставшиеся зоны:

- согласовать и импортировать реальную структуру warehouse locations;
- улучшить UI для больших stocktake sessions;
- добавить carrier labels / tracking integrations, если нужны;
- решить, нужен ли approval workflow для новых/обновленных клиентских товаров;
- улучшить клиентские отчеты после согласования точных колонок;
- добавить более строгие guards для сложных moves/repack/corrections;
- улучшить детальный client-facing discrepancy workflow.

## Автоматические Проверки

В репозитории есть автоматические проверки, которые используются перед передачей стенда на ручное тестирование.

- `erpnext_3pl.validation.site` проверяет DocTypes, поля, роли, права, демо-данные, customer isolation, structured receiving/shipment rows, product sync.
- `scripts/validate_instance.sh` проверяет публичный инстанс, логины и основные страницы.
- `scripts/validate_warehouse_ops.sh` проверяет складские операции: moves, putaway, full/partial repack, invalid repack review, corrections, stocktake, picking, packing, shipping.
- `scripts/validate_mvp_e2e.sh` проверяет полный golden path: client product -> receiving -> putaway -> stocktake -> shipment request -> picking -> packing -> shipping.

Серверные stateful-проверки нужно запускать последовательно, не параллельно, потому что они создают и отменяют временные stock документы.

Эти проверки снижают риск, но не заменяют ручную приемку заказчиком.
