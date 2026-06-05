# 🎬 Roteiro do Vídeo — AstroVita (GS Space Connect)

Duração alvo: **3 a 5 minutos**. Grave a tela mostrando o app rodando + sua narração.

---

## 1. Abertura e problema (0:00 – 0:40)

> "Olá, meu nome é Enzo Miletta, e este é o **AstroVita**, minha solução para a Global Solution **Space Connect** da FIAP.
>
> O tema é tecnologia espacial aplicada a desafios reais. Um dos maiores riscos em missões espaciais e em centros de controle críticos é a **fadiga humana** — um tripulante sonolento ou desatento pode comprometer a missão inteira.
>
> O AstroVita resolve isso usando **Visão Computacional**: com apenas uma webcam, ele monitora a saúde e a atenção da tripulação em tempo real, sem nenhum sensor vestível."

## 2. A proposta / como funciona (0:40 – 1:30)

> "A solução é feita 100% em **Python**, usando **OpenCV** para captura de vídeo e **MediaPipe** para a inferência visual.
>
> Eu uso o **Face Mesh**, que detecta 468 pontos no rosto, e o **Pose**, que detecta a postura dos ombros. A partir desses landmarks eu calculo:
> - o **EAR**, que mede a abertura dos olhos para detectar sonolência;
> - o **MAR**, que detecta bocejos;
> - a **taxa de piscadas por minuto**, sinal de fadiga ocular;
> - e a **inclinação da cabeça e dos ombros**, para avaliar a postura.
>
> Com isso, o sistema classifica o estado em **NOMINAL**, **ATENÇÃO** ou **CRÍTICO**."

## 3. Demonstração ao vivo (1:30 – 3:30)

Mostre o app rodando (`python main.py`) e narre enquanto demonstra:

1. **Estado normal** — olhe para a câmera, postura reta.
   > "Aqui estou em estado NOMINAL: olhos abertos, postura alinhada. Veja o painel lateral com as métricas em tempo real."
2. **Piscadas** — pisque algumas vezes.
   > "O contador de piscadas sobe a cada piscada detectada."
3. **Sonolência** — feche os olhos por ~2 segundos.
   > "Quando fecho os olhos por mais tempo, o sistema dispara o alerta de SONOLÊNCIA e muda para CRÍTICO, com a borda vermelha."
4. **Bocejo** — abra bem a boca.
   > "Ao bocejar, o MAR sobe e o bocejo é contabilizado."
5. **Postura** — incline a cabeça e os ombros.
   > "Inclinando a cabeça ou os ombros, recebo alertas de postura."
6. **Robustez** — mostre funcionando a distâncias diferentes e/ou com a tecla `m` ligando/desligando a malha facial.
   > "A solução é estável em diferentes distâncias e condições. Posso ligar e desligar a malha facial com a tecla M."
7. **Gravação** — pressione `r`.
   > "Com a tecla R eu gravo a sessão, e todas as métricas são salvas em um CSV para análise posterior."

## 4. Aplicação prática e fechamento (3:30 – 4:30)

> "Na prática, o AstroVita poderia rodar de forma autônoma em uma estação espacial ou num centro de controle de satélites, emitindo **alertas precoces de fadiga** antes que o erro humano aconteça — usando apenas uma câmera comum.
>
> Todo o código está no meu repositório público no GitHub, com README e instruções de execução. Obrigado!"

---

## ✅ Checklist antes de gravar
- [ ] Boa iluminação frontal no rosto
- [ ] Webcam funcionando (`python main.py`)
- [ ] Testar fechar olhos / bocejar / inclinar cabeça antes
- [ ] Mostrar o terminal rodando o comando
- [ ] Mostrar rapidamente o repositório no GitHub no final
- [ ] Áudio limpo, fala pausada
