class EstrategiaAnalisis:
    def analizar(self, response):
        pass

class AnalizarConTablas(EstrategiaAnalisis):
    def analizar(self, response):
        # Implementación para analizar tablas
        return "Resultado del análisis de tablas"

class AnalizarConKeyValue(EstrategiaAnalisis):
    def analizar(self, response):
        # Implementación para analizar pares clave-valor
        return "Resultado del análisis de pares clave-valor"
