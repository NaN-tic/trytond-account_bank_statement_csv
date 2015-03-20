#:after:account_bank_statement/account_bank_statement:section:extractos_bancarios#

.. inheritref:: account_bank_statement_csv/account_bank_statement_cav:section:extractos_bancarios_csv

-----------------------
Extractos bancarios CSV
-----------------------

En los extractos bancarios disponemos de un asistente que nos permite seleccionar
un fichero CSV e importar las líneas en el extracto para conciliar.

Algunas plataformas de pagos (Paypal, Redsys, Sermepa, Cofidis,...) sólo permiten
para extraer datos de los pagos mediante ficheros CSV o es el formato más común.

En el caso que sólo permitan exportar los datos en formato XLS (Excel)
deberemos antes de importar el fichero convertirlo en formato CSV, usando
algún programa de ofimática, como LibreOffice.

Al disponer de un fichero CSV, podemos importar en nuestro extracto bancario y así
conciliar los pagos que se han realizado en nuestra plataforma de pago con
los movimientos contables.

En la configuración de extractos bancarios deberemos definir los perfiles CSV que
usaremos como la estructura del CSV (antes deberemos documentar cada campo del CSV
que corresponde y relacionar con un campo de la línea del extracto bancario.

Las líneas del CSV del extracto bancario deberemos definir:

* Campo: Campo de la línea que se guardará la información
* Columnas: Columnas del CSV que corresponden al campo. Podemos juntar varias columnas
  del CSV en una sola columna, por ejemplo, en la descripción. Cada campo del CSV
  que deseamos juntar, será la posición separado con la coma. Ejemplo: 3,10,12
* Formato fecha. En el caso que el campo sea "datetime" anotaremos el formato de la fecha
  que recibimos en el CSV. Ejemplo: %d/%m/%Y,%H:%M:%S

En el caso que el CSV contenga muchas líneas de pagos y no deseamos importar todas estas
líneas, con el campo "Expresión de coincidencia" podemos filtrar las líneas que se importarán.
Esto nos permite por ejemplo en un CSV de Paypal, omitir aquellos pagos que no se hayan
completado y sólo importar los pagos realizados. Un ejemplo de condición seria:

.. code::

    row[5] == "Cancelled" and row[11] == "user@domain.com"

En el caso que coincida la línea del CSV con esta expresión, se omite y continuará con la
siguiente línea del CSV, y no se importará.

"row" es la variable de la línea y entre "[]" especificaremos la posición del campo
(la primera columna del CSV es el 0). En este ejemplo anotamos que la columna 5 contenga la cadena
de texto "Cancelled" y que la columna 11 contenga la cadena de texto "user@domain.com".
