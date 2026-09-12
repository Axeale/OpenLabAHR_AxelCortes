##### Documentación en proceso...
# AHR OPEN LAB by Axel Cortes
### Te preguntarás, ¿Como veras los archivos que cree para el openlab?
**Que buena pregunta**
### Pero primero, ¿Qué fue lo que hice durante esta semana?
## Avance significativo 1 (Primeros días despues de la entevista)
- Cree, y probe el parser, para que imprimira las intents. Ya medio lo vieron jeje.
### ¿Cómo funciona el parser? 
El parser funcione de la sigiente manera:

Primero, tu le das input de texto y lo tokeniza (convierta cada palabra en un elemento de una lista). 

Depues, cada token lo compara con un diccionario de palabras clave, para identificar el objeto que se busca. Por ejemplo: 
Cubo tiene varias maneras de escribirse (Cube, cubo, block, box, etc).

El parser busca en cada una de estas palabras clave, para retornar al objeto que nos estamos refiriendo, que en este caso es un cubo. 
Este proceso lo hace para tnato el Intent (pick, place, drop, etc), para la zona en donde dejarlo, y para saber el color del cubo al que se esta refieiredo. 

Finalmente, se imprie todos los valores que el parser identifico :)

## Avance significativo 2 (Ultimos tres días)
- Uno de mis avances, fue crear una policy para poder mover cada joint por separado, y guardar el angulo exacto en el que quisiera que este. Basicamente es un creador de estados (guarda el vector q) y lo guarda en un json. 
- Otro policy fue para probar estos waypoints, usando interpolacion lineal para que el movimiento se mas suave (tampoco crean que es la gran cosa jaja, no es nada complejo). 
- Cree las demos, para poder ejecutar las policies que queira. 
- Instale *mujoco* en ubuntu, estuvo complejo, pero con ayuda de claude se pueden hacer maravillas jeje. 
- Cree una escena básica para que el humanoide interactue con un cubo basico, y tambien una mesa. (modifique el xml que tenia el mujoco por default)

### ¿Como funcionan estas policy que les acabo de mencionar?
### Policy1: [JointTunerPolicy](/src/g1_playground/policies/movement_testing_tools.py#L74)

Este policy, lo que hace es que en la terminal puedes elegir un joint en especifico, e ir subiendo o bajando la posicion en la que quieres que este ese joint. 

Como mencione antes, se puede guardar el estado actual del robot(todos los joints), y se guardan como un nuevo elemento en un json llamado [waypoints.json](/waypoints.json)

_**Aqui dejo los comandos con los que funcione el tuner:**_

``` Pyhton
j <indice o nombre>  -> selecciona qué articulación vas a mover
      + / -                 -> incrementa/decrementa esa articulación (paso pequeño)
      show                  -> imprime el vector q actual completo
      save <nombre>         -> guarda el q actual en waypoints.json bajo ese nombre
      quit                  -> termina 
```

### Policy2: [PhaseTestPolicy](/src/g1_playground/policies/movement_testing_tools.py#L210)



