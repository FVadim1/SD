


<style>

.celda{
  min-height: 30px;
  min-width: 30px;
  border: solid 1px black ;
  margin: 5px;
  background-color: white;
}

</style>

<!-- Logica de la aplicacion -->
<script>

import axios from 'axios'

let err = ""
let mapa = []
let jugadores = []
setInterval(() => {
  axios.get("https://192.168.22.100:4000/mapa").then((datos)=> {
    //console.log(datos)
    mapa=datos.data
    err = ""
  }).catch((error) => { err = error})
  axios.get("https://192.168.22.100:4000/jugadores").then((datos)=> {
    jugadores=datos.data
    err = ""
  }).catch((error) => { console.log(error)})
}, 1000)


</script>

<div class="container text-center">
{#if err==""}
 {#each mapa as fila , y}

    <div class="d-flex flex-row justify-center {y == 10 ? "mt-3" : ''}">
      {#each fila as elemento, x}
        {#if elemento=='M'}
          <div class="celda" style="background-color: red; color: cornsilk">
            {elemento}
          </div>

        {:else if elemento == 'A'}
        <div class="celda" style="background-color:olivedrab; color:cornsilk">
          {elemento}
        </div> 

        {:else if elemento == '0'}
          {#if y >= 0 && y <= 9 && x >= 0 && x <= 9}
          <div class="celda" style="background-color:lightgray">
            {elemento}
          </div> 
          {/if}
          {#if y  >= 0 && y <= 9 && x >= 10 && x <= 19}
          <div class="celda" style="background-color: lightgray; color: black;">
            {elemento}
          </div> 
          {/if}
          {#if y >= 10 && y <= 19 && x >= 0 && x <= 9}
          <div class="celda" style="background-color: lightgray">
            {elemento}
          </div> 
          {/if}
          {#if y >= 10 && y <= 19 && x >= 10 && x <= 19}
          <div class="celda" style="background-color: lightgray">
            {elemento}
          </div> 
          {/if}
        {:else}
          <div class="celda" style="background-color: cyan">
            {elemento}
          </div>           
        {/if}
          {#if x == 9}
            <div class="mx-2">

            </div>
          {/if}
      {/each}
    </div>
  {:else}
  <h3> Cargando mapa... </h3>
  {/each}

  <ul class="list-group">
  {#each jugadores as fila , y}
  <div class="list-group-item">
    {fila}
  </div>   
  {/each}
  </ul>


  {:else}
<div class="alert alert-danger" role="alert">
  ERROR: No se ha podido obtener dados de la API Engine.
  <pre>
    {err.toString()}
  </pre>
</div>

{/if}
</div>


