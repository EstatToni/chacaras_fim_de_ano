import pandas as pd
import folium
from folium.plugins import MarkerCluster
import streamlit as st
import plotly.graph_objects as go
import requests
import geojson
from shapely.geometry import shape

st.sidebar.header("📍 Digite sua localização")

latitude_usuario = st.sidebar.number_input("Latitude", value=00.000000, format="%.6f", step=0.000001)
longitude_usuario = st.sidebar.number_input("Longitude", value=00.000000, format="%.6f", step=0.000001)
coordenadas_usuario = (latitude_usuario, longitude_usuario)

if latitude_usuario != 0.0 and longitude_usuario != 0.0:

    def calcular_distancia_osrm(origem, destino):
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{origem[1]},{origem[0]};{destino[1]},{destino[0]}?overview=false"
            response = requests.get(url)
            data = response.json()
            distancia_km = data['routes'][0]['legs'][0]['distance'] / 1000  # metros para km
            return round(distancia_km, 2)
        except:
            return None
    
    
    dados = pd.DataFrame({
        "Nome": ["Rancho",
                "Chácara charmosa",
                "Chácara agradável",
                "Casa inteira"],
        "Valor": [3250, 5525, 3888, 4840],
        "Distância (km)": [43, 15, 24, 34],
        "Avaliação": [5, 4.7, 4.89, 4.88],
        "Número de Avaliações": [2, 40, 18, 56],
        "Comodidades": [
        "Piscina, Wi-Fi, Churrasqueira, TV, Mesa de bilhar, Cozinha completa, Microondas, Freezer, Fogão, Forno, Cafeteira, Torradeira, Liquidificador, Assadeira, Utensílios de cozinha, Roupa de cama, Estacionamento, Permitido animais, Acesso ao lago, Quintal, Cadeira espreguiçadeira",
        "Piscina, Jacuzzi, Wi-Fi, Wifi portátil, Espaço de trabalho, TV, Churrasqueira, Cozinha completa, Microondas, Freezer, Fogão, Cafeteira, Refrigerador, Utensílios de cozinha, Taças de vinho, Móveis externos, Área de jantar externa, Quintal, Pátio ou varanda, Cadeira espreguiçadeira, Estacionamento, Entrada privada, Permitido animais, Permitido fumar, Self check-in, Casa térrea, Rede de proteção, Ar-condicionado, Cabides, Cofre de chaves",
        "Piscina, Wi-Fi, TV, Churrasqueira, Cozinha, Refrigerador, Louças e talheres, Cafeteira, Quintal, Fogueira, Área de jantar externa, Estacionamento, Permitido animais, Permitido fumar",
        "Piscina privativa, Wi-Fi, TV a cabo, Mesa de ping pong, Cozinha completa, Refrigerador, Microondas, Lava-louças, Forno, Fogão, Louças e talheres, Cafeteira Nespresso, Utensílios para churrasco, Mesa de jantar, Área de jantar externa, Quintal privativo, Varanda, Parque infantil, Bicicletas infantis, Ventilador de teto, Espaço de trabalho exclusivo, Máquina de lavar, Ferro de passar, Estacionamento, Estacionamento na rua, Permitido fumar, Entrada privada, Self check-in, Rede",
        ],
        "Latitude": [-23.027427, -22.878504, -22.798743, -23.045810],
        "Longitude": [-47.220915, -47.209515, -47.000084, -46.985050],
    })

    # Cálculo da distância
    dados["Distância (km)"] = dados.apply(
        lambda row: calcular_distancia_osrm(coordenadas_usuario, (row["Latitude"], row["Longitude"])),
        axis=1
    )

    # Valores padrão para os filtros
    valor_range = (int(dados["Valor"].min()), int(dados["Valor"].max()))

    dist_range = (
        float(dados["Distância (km)"].min()),
        float(dados["Distância (km)"].max()),
    )
    avaliacao_minima = float(dados["Avaliação"].min())

    todas_comodidades = pd.Series(
        ", ".join(dados["Comodidades"]).split(", ")
    ).unique()

    # Função para resetar filtros
    if st.sidebar.button("🔄 Limpar filtros"):
        st.session_state["valor"] = valor_range
        st.session_state["distancia"] = dist_range
        st.session_state["avaliacao"] = avaliacao_minima
        st.session_state["comodidade"] = []

    # Filtros na sidebar
    st.sidebar.header("Filtros adicionais")

    valor_min, valor_max = st.sidebar.slider(
        "Faixa de valor (R$)",
        min_value=valor_range[0],
        max_value=valor_range[1],
        value=st.session_state.get("valor", valor_range),
        step=100,
        key="valor",
    )

    dist_min, dist_max = st.sidebar.slider(
        "Faixa de distância (km)",
        min_value=dist_range[0],
        max_value=dist_range[1],
        value=st.session_state.get("distancia", dist_range),
        step=0.1,
        key="distancia",
    )

    avaliacao_min = st.sidebar.slider(
        "Avaliação mínima (estrelas)",
        min_value=float(dados["Avaliação"].min()),
        max_value=float(dados["Avaliação"].max()),
        value=st.session_state.get("avaliacao", avaliacao_minima),
        step=0.1,
        key="avaliacao",
    )

    comodidade = st.sidebar.multiselect(
        "Filtrar por comodidades:",
        options=todas_comodidades,
        default=st.session_state.get("comodidade", []),
        key="comodidade",
    )

    # Aplicar filtros
    dados_filtrados = dados[
        (dados["Valor"] >= valor_min)
        & (dados["Valor"] <= valor_max)
        & (dados["Distância (km)"] >= dist_min)
        & (dados["Distância (km)"] <= dist_max)
        & (dados["Avaliação"] >= avaliacao_min)
    ]

    if comodidade:
        dados_filtrados = dados_filtrados[
            dados_filtrados["Comodidades"].apply(
                lambda x: all(c in x for c in comodidade)
            )
        ]

    # Calcular o custo-benefício (menor é melhor)
    dados_filtrados["Custo-benefício"] = dados_filtrados["Valor"] / (dados_filtrados["Avaliação"] * (dados_filtrados["Distância (km)"] + 1))

    # Melhor custo-benefício (menor valor de custo-benefício)
    melhor_custo_beneficio = dados_filtrados.loc[dados_filtrados["Custo-benefício"].idxmin()]

    # Mais perto (menor distância)
    mais_perto = dados_filtrados.loc[dados_filtrados["Distância (km)"].idxmin()]

    # Melhor avaliada (maior avaliação)
    melhor_avaliada = dados_filtrados.loc[dados_filtrados["Avaliação"].idxmax()]

    st.markdown("### Chácaras Filtradas")
    cor_fundo = "#1E1E1E"  # tom escuro para combinar com o tema dark
    cor_caixa = "#2C2C2C"  # um pouco mais clara pra destacar
    cor_texto = "#F0F0F0"

    col1, col2, col3 = st.columns(3)

    for i, (index, row) in enumerate(dados_filtrados.iterrows()):
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(
                f"""
                <div style="
                    background-color: {cor_caixa}; 
                    border-radius: 12px; 
                    padding: 16px; 
                    margin-bottom: 20px; 
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    color: {cor_texto};
                ">
                    <h4 style="margin-top: 0; color: {cor_texto};">{row['Nome']}</h4>
                    <img src="https://picsum.photos/300/180?random={i}" 
                        style="width: 100%; height: auto; border-radius: 8px; margin-bottom: 10px;">
                    <p><strong>Valor:</strong> R$ {row['Valor']}</p>
                    <p><strong>Avaliação:</strong> {row['Avaliação']} ⭐</p>
                    <p><strong>Distância:</strong> {row['Distância (km)']} km</p>
                    <p><strong>Comodidades:</strong> {', '.join(row['Comodidades'].split(', ')[:4])}...</p>
                    <a href="#" style="text-decoration: none; color: #4EA8DE;">Ver mais</a>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Exibindo os destaques
    st.markdown("### Destaques Automáticos")
    st.write(f"**Melhor Custo-Benefício:** {melhor_custo_beneficio['Nome']} - R${melhor_custo_beneficio['Valor']}")
    st.write(f"**Mais Perto:** {mais_perto['Nome']} - Distância: {mais_perto['Distância (km)']} km")
    st.write(f"**Melhor Avaliada:** {melhor_avaliada['Nome']} - Avaliação: {melhor_avaliada['Avaliação']} estrelas")

    # Função para calcular a rota entre dois pontos usando a API OSRM
    def get_route(start_coords, end_coords):
        # Formatar a URL para a API OSRM
        url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full&geometries=geojson"
        
        # Fazer a requisição à API
        response = requests.get(url)
        data = response.json()
        
        # Extrair a geometria da rota
        route_geometry = data['routes'][0]['geometry']
        
        # Extrair distância e tempo estimado da rota
        distance = data['routes'][0]['legs'][0]['distance'] / 1000  # em km
        duration = data['routes'][0]['legs'][0]['duration'] / 60  # em minutos
        
        return route_geometry, distance, duration

    # Criando o mapa
    m = folium.Map(
        location=[dados["Latitude"].mean(), dados["Longitude"].mean()],
        zoom_start=13,
        control_scale=True,
        tiles="CartoDB positron"
    )

    # Adicionando o marcador personalizado para sua casa
    folium.Marker(
        location=coordenadas_usuario,
        popup="Minha Casa",
        icon=folium.Icon(color="green", icon="home", prefix="fa")
    ).add_to(m)

    # Adicionando MarkerCluster para as chácaras
    marker_cluster = MarkerCluster().add_to(m)

    # Adicionando marcadores de localização das chácaras
    for i, row in dados.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=row["Nome"],
            icon=folium.Icon(color="blue", icon="info-sign", prefix="fa"),
        ).add_to(marker_cluster)

    # Adicionando um filtro para selecionar rotas na sidebar
    rotas_selecionadas = []
    st.sidebar.markdown("### Selecione as rotas para visualizar")

    for i, row in dados.iterrows():
        selected = st.sidebar.checkbox(f"Mostrar rota para {row['Nome']}", key=f"rota_{i}")
        if selected:
            rotas_selecionadas.append(i)

    # Exibindo as rotas selecionadas
    for i in rotas_selecionadas:
        end_coords = [dados.iloc[i]["Latitude"], dados.iloc[i]["Longitude"]]  
        route_geometry, distance, duration = get_route(coordenadas_usuario, end_coords)  

        # Adicionando a rota ao mapa
        folium.GeoJson(route_geometry, name=f"Rota para {dados.iloc[i]['Nome']}").add_to(m)
        
        # Exibindo a distância e o tempo estimado na interface do Streamlit
        st.sidebar.markdown(f"**Rota para {dados.iloc[i]['Nome']}**")
        st.sidebar.markdown(f"**Distância**: {distance:.2f} km")
        st.sidebar.markdown(f"**Tempo estimado**: {duration:.2f} minutos")

    # **Calculadora de Gasolina**
    st.sidebar.markdown("### Calculadora de Gasolina")

    # Input de preço da gasolina (em R$)
    preco_gasolina = st.sidebar.number_input("Preço da gasolina (R$/litro)", min_value=0.0, value=5.5, step=0.1)

    # Input de distância (em km)
    distancia = st.sidebar.number_input("Distância a ser percorrida (km)", min_value=0.0, value=50.0, step=1.0)

    # Input de eficiência do carro (km/litro)
    eficiencia = st.sidebar.number_input("Eficiência do carro (km/litro)", min_value=0.0, value=10.0, step=0.1)

    # Cálculo de litros necessários e valor gasto com gasolina
    if eficiencia > 0:
        # Calcular quantos litros de gasolina serão necessários
        litros_necessarios = distancia / eficiencia  # em litros
        valor_gasto = litros_necessarios * preco_gasolina  # em R$

        # Exibindo os resultados na sidebar
        st.sidebar.markdown(f"**Litros de gasolina necessários**: {litros_necessarios:.2f} L")
        st.sidebar.markdown(f"**Valor estimado de gasolina**: R${valor_gasto:.2f}")
    else:
        st.sidebar.markdown("**Por favor, insira um valor válido para a eficiência do carro.**")

    # Exibindo o mapa
    map_html = m._repr_html_()
    st.markdown("### Localização das Chácaras com Rotas")
    st.components.v1.html(map_html, height=500)

    st.markdown("## 📍 Detalhes da Chácara Selecionada")

    # Filtra somente as rotas selecionadas no checkbox (baseado na sidebar)
    chacaras_visiveis = dados_filtrados.loc[rotas_selecionadas]

    # Dicionário com as informações por chácara
    info_chacaras = {
        "Rancho": {
            "descricao": """Seja bem-vindo ao nosso sítio em Indaiatuba, o destino perfeito para quem busca descanso, lazer e contato com a natureza.

    Nossa propriedade oferece:

    ✔️ Piscina para se refrescar nos dias quentes  
    ✔️ Lago para pesca para quem gosta de tranquilidade  
    ✔️ Área de churrasqueira  
    ✔️ 3 suítes aconchegantes, equipadas para proporcionar conforto e uma ótima noite de sono

    Localizado em um ambiente cercado por muito verde, nosso sítio proporciona a combinação perfeita entre lazer e descanso.""",
            "imagens": [
                "imagens/rancho1.png"
            ]
        },
        "Chácara charmosa": {
            "descricao": """O espaço está localizado em uma região central próximo a supermercados, bancos, bares e avenidas movimentadas, porém com toda a tranquilidade de um bairro seguro e calmo.

    ATENÇÃO:

    a propriedade conta com 3 quartos sendo:

    01 Suíte
    01 quarto com cama de casal
    01 quarto com 2 camas de solteiro;
    01 colchão inflável.
    02 banheiros externos anexos aos dois quartos além do banheiro suíte.

    01 salão com meda e cadeiras anexo à área gourmet.
    O espaço
    A propriedade possui câmeras na área externa.
    Outras observações
    Para uso da Jacuzzi interna, consultar previamente pois implica em taxas adicionais conforme quantidade de dias e número de hóspedes.

    Streaming de filme disponível: Watch Paramount +

    Maquina de Cafe: Três Corações (reposição de cápsula solicitada com antecedência e faturada extraordinariamente conforme pedido)

    Sofa: Tecido Suede, caso constatado pelo animal, manchas, derramamento de líquidos, será solicitado valor correspondente a higienizacao.

    aquecedor: Alimentação 220v

    Roupas de cama e Toalhas: será fornecido apenas forração como lençol e capas para travesseiro.

    Toalha apenas de rosto.

    PROIBIDO ANIMAIS / PETS NA PISCINA, INDEPENDENTE DA RAÇA/ ESPÉCIE.

    PROIBIDO VIDROS E ALIMENTOS NA PISCINA;

    PROIBIDO SOM ALTO A QUALQUER HORA DO DIA.

    EM CASO DE CHUVA E VENTO: RECOLHA OS TOLDO E GUARDA SOL.""",
            "imagens": [
                "imagens/chacara2_1.jpg",
                "imagens/chacara2_2.jpg"
            ]
        },
        "Chácara agradável": {
            "descricao": """Relaxe com toda a família nesta acomodação tranquila.
    Chacara com conforto e mercado na esquina.
    Aproveite a tranquilidade e a natureza a 15 km da cidade, num bairro de chacaras.
    Wi Fi TV Piscina Churrasqueira
    O espaço
    sala cozinha varanda 3 quartos
    2 camas de casal
    1 cama box de solteiro
    1 cama de solteiro com cama auxiliar
    1 sofá cama de casal
    1 colchão inflável de casal ( pode ser usado na piscina)
    2 redes
    sanduicheira
    cafeteira elétrica
    churrasqueiras
    micro-ondas
    espremedor de laranja
    fogao 4 bocas e forno
    geladeira""",
            "imagens": [
                "imagens/chacara3_1.jpg",
                "imagens/chacara3_2.jpg"
            ]
        },
        "Casa inteira": {
            "descricao": """A casa fica dentro do condomínio Marambaia, em Vinhedo. É toda plana, com exceção do espaço da churrasqueira/forno à lenha, que é acessado por escada. Contém 2 quartos de casal, 1 quarto de solteiro com duas camas box e 2 colchões extra novos (de solteiro), totalizando 8 pessoas acomodadas. Também conta com 2 salas, ambiente externo com churrasqueira e forno à lenha (pizza \o/), piscina exclusiva e garagem para 3 carros.
    O espaço
    A casa tem uma vista incrível, ideal para encontros familiares, já que é um ambiente muito aconchegante.

    Na casa você encontra:
    -Roupas de Cama e Banho, Cobertores e Travesseiros
    -Itens básicos de higiene e limpeza
    -Camas de casal de molas
    -SmartTV, Netflix com home theater
    -Ar condicionado
    -Wi-fi
    -Utensílios para fazer pizza no forno à lenha e para churrasco
    -Cafeteira Nespresso
    -Lava-louças
    -Máquina de lavar roupa

    Observações muito importantes:

    - Não é permitido festas e som alto. O condomínio e a vizinhança são totalmente familiares e, portanto, não é o ambiente adequado para isso.
    Acesso do hóspede
    Acesso total e particular a todas as áreas do terreno, incluindo piscina, churrasqueira e forno à lenha.
    Outras observações
    Todas as tomadas 220V.""",
            "imagens": [
                "imagens/chacara4_1.jpg",
                "imagens/chacara4_2.jpg"
            ]
        }
    }

    # Lista de nomes das chácaras visíveis que também existem no dicionário
    nomes_visiveis = [nome for nome in chacaras_visiveis["Nome"] if nome in info_chacaras]

    # Se houver chácara visível, mostra os detalhes
    if nomes_visiveis:
        chacara_selecionada = st.selectbox("Selecione uma chácara para ver detalhes", nomes_visiveis)

        st.markdown(f"### {chacara_selecionada}")
        st.markdown(info_chacaras[chacara_selecionada]["descricao"])
        
        # Pega os dados da chácara original (linha do dataframe)
        dados_chacara = chacaras_visiveis[chacaras_visiveis["Nome"] == chacara_selecionada].iloc[0]

        st.markdown(f"**💰 Valor:** R${dados_chacara['Valor']}")
        st.markdown(f"**📏 Distância:** {dados_chacara['Distância (km)']} km")
        st.markdown(f"**⭐ Avaliação:** {dados_chacara['Avaliação']} ({dados_chacara['Número de Avaliações']} avaliações)")

        # Mostra imagens
        #st.image(info_chacaras[chacara_selecionada]["imagens"], use_column_width=True)
    else:
        st.info("Selecione pelo menos uma chácara na barra lateral para visualizar os detalhes.")
else:
    st.warning("Por favor, insira suas coordenadas para visualizar o dashboard.")
