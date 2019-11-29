# PERSONALIZACIONES STOCK
 - Control de lotes en silos: Si ya hay un lote diferente se mezcla

## ESPECIFICACIÓN
Cuando se mueve mercancía a una ubicación de silo, hay que comprobar si ya existía un lote, y si es así hay que mezclar ambos lotes. El resultado será un nuevo lote por la cantidad total.
Esta mezcla se hará con una orden de producción, que coja toda la cantidad con sus lotes que haya en un silo y la lleve a la ubicación de Consumo de
mezclas, El producto finalizado saldrá de Mezclas hacia el silo de nuevo, con el nuevo lote

## DESARROLLO
Módulo **custom_stock**.
En **stock.picking** se hereda el action done y se buscan las ubicaciones que necesitan mezclarse, es decir, aquellas que son tipo silo y tienen más de un lote.
Para todas estas ubicaciones llamo a la función que crea una producción que representa la mezcla. (Esta producción consumirá todo lo que haya en el silo y lo llevara a una nueva ubicación de mezclas), y creará el producto nuevo, con un nuevo lote en la ubicación del silo.

En el **stock.location** se añade la función que crea la producción de mezcla, la idea es tener como materiales de consumo todos los lotes del silo y como producto finalizado el mismo pero con nuevo lote. La cantidad de la producción será igual a toda la cantidad del silo.
Una vez creada la producción se finaliza sola llamando al asistente de producir, y queda realizada. Se guarda en las producciones creadas el albarán que las origina

En el **mpr.poduction**, tuve que heredar la función de _generate_moves, para que si en contexto le llega que es mezcla haga la lógica de crear los movimienmtos de mezcla, y no el super. Tiene un nuevo campo de mezcla desde, que enlaza con el albarán

El asistente de producir **mrp.production.produce** tuve que sobrescribir el onchange de cantidad para que no filtre los consumos por línea de lista de materiales

Se añade una nueva ubicación de Mezcla de lotes y un tipo de operación para las mezclas.
La idea es que los productos que se mezclen deben tener como ubicación de producción la de las mezclas

## TODO
 - Revisar si detecta bien que hay mas de un lote
 - Debería hacer un force asign de los materiales consumidos?
 - Controlar que haya lista de materiales?
 - Atajo desde el alabarán o el move line a las mezclas creadas?
 - En create_production_merge debo buscar quants con qty > 0?
