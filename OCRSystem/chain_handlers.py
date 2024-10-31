class Manejador:
    def set_siguiente(self, siguiente):
        self.siguiente = siguiente

    def manejar(self, response):
        if self.siguiente:
            return self.siguiente.manejar(response)
        return response

class MapWordIdManejador(Manejador):
    def manejar(self, response):
        
        word_map = {}
        
        if self.siguiente:
            return self.siguiente.manejar((response, word_map))
        return response, word_map