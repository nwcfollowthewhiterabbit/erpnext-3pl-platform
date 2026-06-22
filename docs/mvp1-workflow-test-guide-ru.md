# MVP1 Workflow Test Guide

Краткая инструкция для ручного тестирования MVP1 на текущем ERPNext стенде.

## Главное Правило

`Inbound Shipment Notice` не является фактическим поступлением товара на склад.

Это предварительное уведомление от клиента: что клиент ожидает отправить на склад.

Остатки в `Current Inventory` появляются только после складской приемки, когда склад создает фактическое поступление:

- через `Receiving Scan`; или
- через стандартный ERPNext `Stock Entry` типа `3PL Inbound Receipt`.

Если клиент создал только `Inbound Shipment Notice`, но склад еще не сделал приемку, то `Current Inventory` может быть пустым. Это корректное поведение.

## Что Не Входит В MVP1 Тестирование

Не тестировать как часть MVP1:

- `Product Import` / bulk import товаров;
- массовую загрузку товаров из CSV/Excel;
- автоматические carrier labels;
- внешние courier/tracking integrations;
- quantity-level reservation внутри одной большой смешанной коробки.

`Product Import` может существовать в системе как roadmap/admin capability, но для текущего MVP1 клиент работает с товарами через создание и редактирование `Products` / `Three PL Client Product`.

`Product Export` можно использовать для просмотра/выгрузки товаров, но это не означает, что bulk import входит в MVP1.

## Роли Документов

| Документ / Экран | Кто использует | Для чего нужен | Влияет на остатки? |
| --- | --- | --- | --- |
| `Three PL Client Product` / Products | Клиент | Справочник товаров клиента | Нет |
| `Inbound Shipment Notice` | Клиент | Уведомить склад о будущем поступлении товара | Нет |
| `Receiving Scan` | Склад | Быстро принять товар, создать контейнер, Stock Entry и движение | Да |
| `Stock Entry` / `3PL Inbound Receipt` | Склад / менеджер | Нативная ERPNext приемка товара на склад | Да |
| `Three PL Container` | Склад | Физическая коробка / handling unit, где лежит товар | Косвенно, через linked stock |
| `Three PL Container Move` | Склад | Перемещение контейнера между локациями | Меняет локацию контейнера |
| `Three PL Warehouse Correction` | Склад | Исправить количество или состояние товара в контейнере | Да, если есть quantity delta |
| `Three PL Stocktake` | Склад | Инвентаризация / пересчет фактического количества | Да, если есть расхождение |
| `Three PL Shipment Request` | Клиент | Запросить отгрузку товара со склада | Не сразу |
| `Pick List` | Склад | Подобрать товар под отгрузку | Резервирует/готовит picking |
| `Outbound Fulfillment` | Склад | Packing / Shipping | Да, после shipping |
| `Current Inventory` | Клиент | Посмотреть текущие доступные остатки | Только отчет |
| `Operation Turnover` | Клиент / склад | История операций за период | Только отчет |

## MVP1 Flow 1. Приемка Товара

### 1. Клиент Создает Уведомление

Логин: клиент Alpha.

Открыть:

`/desk/3pl-client`

Действия:

1. Открыть `Receiving Notices`.
2. Создать новый `Inbound Shipment Notice`.
3. Указать клиента `Demo Client Alpha`.
4. Указать внешний номер / reference, например `TEST-IN-001`.
5. Добавить товары в `Expected Products`, например:
   - `SKU-ALPHA-001`;
   - expected qty `5`;
   - UOM `Nos`.
6. Сохранить документ.

Ожидаемый результат:

- документ создан;
- склад видит ожидаемую поставку;
- `Current Inventory` еще не обязан измениться.

### 2. Склад Принимает Фактический Товар

Логин: Warehouse Operator или Warehouse Manager.

Открыть:

`/warehouse/receiving`

Действия:

1. В `Receiving Notice / ASN` указать имя Notice или внешний reference, например `TEST-IN-001`.
2. В `Container / HU` указать новый код коробки, например `BOX-TEST-IN-001`.
3. В `Item / SKU` указать `SKU-ALPHA-001`.
4. В `Qty` указать фактически принятое количество, например `5`.
5. В `Receiving Location` оставить `Temporary Receiving - 3`.
6. `Condition` оставить `OK`, если товар без проблем.
7. Нажать `Submit Receipt`.

Ожидаемый результат:

- создается submitted `Stock Entry` типа `3PL Inbound Receipt`;
- создается или обновляется `Three PL Container`;
- создается movement history с типом `Received`;
- `Inbound Shipment Notice` получает `Received Qty`;
- если количество совпало, Notice становится `Received`;
- `Current Inventory` начинает показывать принятый товар.

### 3. Проверка Приемки

Проверить:

1. Открыть `Three PL Container`.
2. Найти контейнер `BOX-TEST-IN-001`.
3. Убедиться, что:
   - client = `Demo Client Alpha`;
   - location = `Temporary Receiving - 3`;
   - внутри есть `SKU-ALPHA-001`;
   - qty = `5`.
4. Открыть клиентом `Current Inventory`.
5. Убедиться, что товар появился в остатках клиента.

## MVP1 Flow 2. Перемещение По Складу

Логин: Warehouse Operator или Warehouse Manager.

Открыть:

`/warehouse/container-move`

Действия:

1. Ввести контейнер из предыдущего flow, например `BOX-TEST-IN-001`.
2. Target location: `Aisle B - 3`.
3. Нажать apply / submit move.

Ожидаемый результат:

- создается `Three PL Container Move`;
- создается movement history;
- контейнер меняет location на `Aisle B - 3`;
- клиентские остатки остаются по тому же товару, но location/container могут измениться в отчетах.

## MVP1 Flow 3. Отгрузка Заказа

### 1. Клиент Создает Shipment Request

Логин: клиент Alpha.

Открыть:

`/desk/3pl-client`

Действия:

1. Открыть `Shipment Requests`.
2. Создать новый `Three PL Shipment Request`.
3. Добавить товар, который уже есть в `Current Inventory`, например `SKU-ALPHA-001`.
4. Указать qty меньше или равно доступному остатку.
5. Сохранить документ.

Ожидаемый результат:

- клиентская заявка на отгрузку создана;
- склад может подобрать товар.

### 2. Склад Выполняет Picking / Packing / Shipping

Логин: Warehouse Manager.

Проверить:

1. Открыть `Pick List` или складской workflow для outbound.
2. Убедиться, что товар берется из существующего контейнера.
3. Подтвердить picking.
4. Выполнить packing/shipping через `Outbound Fulfillment`.

Ожидаемый результат:

- shipment request меняет статус по workflow;
- контейнер/товар участвует в picking;
- после shipping остаток клиента уменьшается.

## MVP1 Flow 4. Коррекция Количества

Логин: Warehouse Operator или Warehouse Manager.

Открыть:

`/warehouse/correction`

Действия:

1. Указать контейнер, например `BOX-TEST-IN-001`.
2. Указать item, например `SKU-ALPHA-001`.
3. Указать фактическое количество.
4. Выбрать тип correction.
5. Нажать apply.

Ожидаемый результат:

- создается `Three PL Warehouse Correction`;
- container contents обновляются;
- если количество изменилось, создается stock adjustment;
- `Current Inventory` отражает новое количество.

## MVP1 Flow 5. Инвентаризация

Логин: Warehouse Operator или Warehouse Manager.

Открыть:

`/warehouse/stocktake`

Действия:

1. Указать stocktake session reference, например `ST-TEST-001`.
2. Указать контейнер.
3. Указать item.
4. Указать counted qty.
5. Нажать apply.

Ожидаемый результат:

- создается `Three PL Stocktake`;
- если counted qty совпадает с системой, статус `No Difference`;
- если есть расхождение, создается связанная correction;
- `Current Inventory` обновляется при quantity delta.

## MVP1 Reports

Клиент проверяет в `3PL Client` workspace:

- `Current Inventory`: текущий остаток по своему клиенту;
- `Inventory By Date`: остаток на дату;
- `Operation Turnover`: операции склада за период;
- `Shipment Tracking`: статусы отгрузок.

Ожидаемый результат:

- клиент видит только `Demo Client Alpha`;
- клиент не видит `Demo Client Beta`;
- отчеты начинают показывать данные только после фактических складских операций.

## Частые Ошибки При Тестировании

1. Создали `Inbound Shipment Notice`, но не сделали receiving.

Результат: `Current Inventory` пустой.

Это нормально. Нужно выполнить `Receiving Scan` или submitted `Stock Entry`.

2. Пытаются переместить контейнер, которого еще нет.

Результат: `Container Move` не может быть выполнен.

Нужно сначала принять товар в контейнер через receiving.

3. В `Receiving Scan` указали reference Notice, но item не существует или принадлежит другому клиенту.

Результат: система блокирует приемку.

Нужно использовать SKU клиента `Demo Client Alpha`.

4. Shipment Request создается на товар, которого нет в Current Inventory.

Результат: склад не сможет корректно подобрать товар.

Сначала нужно принять товар на склад.

5. В `Stock Entry` пытаются вручную менять поле `Purpose`.

Результат: тестер думает, что это обязательное ручное поле.

Это поле только для проверки и должно быть read-only. Нужно выбрать правильный `Stock Entry Type`: для приемки `3PL Inbound Receipt`. Система сама покажет `Purpose = Material Receipt`.
