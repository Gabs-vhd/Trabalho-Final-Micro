#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- Configurações ---
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Pinos do Joystick
const int JOYSTICK_X_PIN = A0;
const int JOYSTICK_Y_PIN = A1;
const int JOYSTICK_BTN_PIN = 2;

// NOVO: Pino para o botão de tiro externo
const int SHOOT_BTN_PIN = 3;

// Variáveis para guardar o estado do jogo recebido do Python
int weaponHeat = 0;
int playerLives = 3;

// --- Custom Characters ---
byte heart[8] = {
  0b00000,
  0b01010,
  0b11111,
  0b11111,
  0b01110,
  0b00100,
  0b00000,
  0b00000
};

void setup() {
  Serial.begin(115200);

  // Configura os pinos dos botões com resistor de pull-up interno
  pinMode(JOYSTICK_BTN_PIN, INPUT_PULLUP);
  pinMode(SHOOT_BTN_PIN, INPUT_PULLUP); // NOVO

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.createChar(0, heart);

  lcd.setCursor(0, 0);
  lcd.print("Conectando ao ");
  lcd.setCursor(0, 1);
  lcd.print("Mustang P-51...");
  delay(2000);
  lcd.clear();
}

void loop() {
  // 1. LER E ENVIAR DADOS DO JOYSTICK E DO NOVO BOTÃO PARA O PYTHON
  int joyX = analogRead(JOYSTICK_X_PIN);
  int joyY = analogRead(JOYSTICK_Y_PIN);
  int joyBtn = digitalRead(JOYSTICK_BTN_PIN);
  int shootBtn = digitalRead(SHOOT_BTN_PIN); // NOVO: Lê o estado do botão de tiro

  // MODIFICADO: Agora enviamos 4 valores
  Serial.print(joyX);
  Serial.print(",");
  Serial.print(joyY);
  Serial.print(",");
  Serial.print(joyBtn); // Mantemos o botão do joystick, talvez para uma bomba no futuro?
  Serial.print(",");
  Serial.print(shootBtn); // Adicionamos o novo botão
  Serial.println(); 

  // 2. RECEBER DADOS DE ESTADO DO JOGO DO PYTHON
  if (Serial.available() > 0) {
    String dataFromPython = Serial.readStringUntil('\n');
    sscanf(dataFromPython.c_str(), "H:%d,L:%d", &weaponHeat, &playerLives);
  }

  // 3. ATUALIZAR O DISPLAY LCD
  updateLCD();

  delay(50);
}

void updateLCD() {
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(weaponHeat);
  lcd.print("%   "); 

  lcd.setCursor(0, 1);
  lcd.print("Vidas: ");
  lcd.write((byte)0);
  lcd.print(" x");
  lcd.print(playerLives);
  lcd.print(" ");
}