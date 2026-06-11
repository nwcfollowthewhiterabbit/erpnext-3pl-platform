# ERPNext 3PL MVP1/MVP2 Acceptance Guide

Документ для ручной проверки текущего состояния MVP1 и MVP2.

Цель: быстро пройти основные клиентские и складские процессы, понять что уже реализовано, где это находится, и какой результат считается корректным.

## Доступы

Стенд:

`https://erpnext.77.237.244.169.sslip.io`

Пароли не хранятся в репозитории. Использовать значения из серверного `.env`.

| Роль | Логин | Пароль | Назначение |
| --- | --- | --- | --- |
| Клиент | `alpha.client@example.test` | `CLIENT_PORTAL_PASSWORD` | Клиентский портал, клиент `Demo Client Alpha` |
| Warehouse Operator | `warehouse.demo@example.test` | `WAREHOUSE_OPERATOR_PASSWORD` | Операционные складские действия |
| Warehouse Manager | `warehouse.manager@example.test` | `WAREHOUSE_MANAGER_PASSWORD` | Складские действия + review очереди |
| Business Owner | `BUSINESS_OWNER_USER` | `BUSINESS_OWNER_PASSWORD` | Владелец/администратор системы |
| Administrator | `Administrator` | `ADMIN_PASSWORD` | Полный системный администратор |

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

`/client/products/list`

Бизнес-уникальность товара:

`Client + Client SKU`

ERPNext `Item` остается системной складской карточкой. Клиент работает с `Three PL Client Product`, а синхронизация создает/обновляет ERPNext `Item`.

Клиент может:

- создать товар;
- обновить товар;
- добавить описание, UOM, barcode, фото;
- деактивировать товар вместо удаления;
- импортировать товары CSV/XLSX;
- экспортировать товары CSV.

### Клиентские Заявки

Receiving Notice и Shipment Request больше не должны быть просто текстовым описанием товаров.

В клиентском портале товары выбираются из активных синхронизированных карточек клиента через поиск по SKU/названию. Система затем разворачивает выбранные строки в child tables:

- `Inbound Shipment Notice Item`;
- `Three PL Shipment Request Item`.

Служебное поле `portal_items_description` оставлено для совместимости и хранения structured JSON.

## Клиентский Портал

Стартовые ссылки:

- Receiving Notices: `/client/receiving-notice/list`
- Products: `/client/products/list`
- Product Imports: `/client/product-import/list`
- Product Export: `/client/product-export`
- Inventory: `/client/inventory/list`
- Shipment Requests: `/client/shipment-request/list`
- Shipment Tracking: `/client/shipment-tracking`
- Discrepancies: `/client/discrepancies`
- Discrepancy Instructions: `/client/discrepancy-instruction/list`

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

1. Открыть `/client/products/list`.
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

1. Открыть `/client/product-export`.
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
4. Открыть `/client/product-import/list`.
5. Загрузить CSV/XLSX.

Ожидаемый результат:

- создается `Three PL Client Product Import`;
- после processing статус становится `Applied` или `Failed`;
- успешные строки создают/обновляют товары;
- товары синхронизируются в ERPNext `Item`;
- ошибки видны в `Error Log`.

### TC-P05: Экспорт Товаров

Роль: клиент.

Шаги:

1. Открыть `/client/product-export`.
2. Нажать `Download Products CSV`.

Ожидаемый результат:

- скачивается CSV со своими товарами клиента;
- товары другого клиента не попадают в экспорт.

## MVP1. Receiving Flow

### TC-R01: Клиент Создает Receiving Notice

Роль: клиент.

Шаги:

1. Открыть `/client/receiving-notice/new`.
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

1. Открыть `/warehouse/receiving`.
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

1. Открыть `/client/discrepancies`.
2. Найти discrepancy по своему notice.
3. Открыть `/client/discrepancy-instruction/list`.
4. Создать instruction для warehouse.

Ожидаемый результат:

- клиент видит только свои discrepancies;
- клиент может отправить инструкцию;
- инструкция сохраняется как `Three PL Client Instruction`.

## MVP1. Putaway And Location Movement

### TC-L01: Putaway Из Receiving В Storage

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть `/warehouse/putaway`.
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

1. Открыть `/warehouse/container-move`.
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

1. Открыть `/client/shipment-request/new`.
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

1. Открыть `/warehouse/picking-confirmation`.
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

1. Открыть `/warehouse/outbound-fulfillment`.
2. Указать shipment request / reference.
3. Указать container.
4. Выполнить packing или shipping step.

Ожидаемый результат:

- создается/обновляется Stock Entry для packing/shipping;
- shipment request получает актуальный status;
- container movement history обновляется;
- клиент видит status в `/client/shipment-tracking`.

## MVP1. Corrections

### TC-C01: Quantity Correction

Роль: Warehouse Operator или Warehouse Manager.

Шаги:

1. Открыть `/warehouse/correction`.
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

1. Открыть `/warehouse/correction-review`.
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

1. Открыть `/warehouse/stocktake`.
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

1. Открыть `/client/inventory/list`.
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

1. Открыть inventory.
2. Открыть receiving notices.
3. Открыть shipment requests.
4. Открыть products.
5. Попробовать найти `Demo Client Beta`, `SKU-BETA-001`, `ASN-BETA-001`.

Ожидаемый результат:

- Beta данные не видны;
- клиент не может создать запись для другого Customer;
- нет скрытых ошибок `Not permitted` на страницах, которые доступны из меню.

## Smoke Checks После Любых Изменений

Перед передачей заказчику полезно прогнать:

1. `/client/receiving-notice/list`
2. `/client/receiving-notice/new`
3. `/client/products/list`
4. `/client/product-import/list`
5. `/client/product-export`
6. `/client/inventory/list`
7. `/client/shipment-request/list`
8. `/client/shipment-request/new`
9. `/client/discrepancies`
10. `/client/discrepancy-instruction/list`
11. `/warehouse/receiving`
12. `/warehouse/putaway`
13. `/warehouse/container-move`
14. `/warehouse/correction`
15. `/warehouse/stocktake`
16. `/warehouse/picking-confirmation`
17. `/warehouse/outbound-fulfillment`

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

В репозитории есть автоматические проверки, которые уже используются при деплое:

- `scripts/validate_site.py` проверяет DocTypes, поля, роли, права, демо-данные, customer isolation, structured receiving/shipment rows, product import/sync.
- `scripts/validate_instance.sh` проверяет публичный инстанс, логины и основные страницы.
- `tests/client_portal.spec.js` проверяет портал в браузере: страницы без permission errors, сохранение login session, auto-filled references, product search picker.

Эти проверки снижают риск, но не заменяют ручную приемку заказчиком.
