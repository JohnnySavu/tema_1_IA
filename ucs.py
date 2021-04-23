import copy
import time
import sys

global_time = 0
output_name_bias = ""
max_in_memory = 0
succ_generated = 0
initial_time = 0


# din laborator
class NodParcurgere:
    def __init__(self, info, cost, parinte, move=None):
        self.info = info
        self.parinte = parinte  # parintele din arborele de parcurgere
        self.g = cost  # acesta este costul
        self.move = move

    def obtineDrum(self):
        l = [self]
        nod = self
        while nod.parinte is not None:
            l.insert(0, nod.parinte)
            nod = nod.parinte
        return l

    # afisez nodul impreuna cu mutarea din care acesta provine.
    # prin afisarea nodului inteleg afisarea vectorului de apa
    # primeste ca parametru un pointer catre un fisier in care sa afiseze
    # nu intoare nimic
    def afisNode(self, file):
        if self.move is not None:
            de_afis = "Din vasul " + str(self.move[0]) + \
                      " s-au turnat " + str(self.move[1]) + " litri de apa de culoare " + \
                      self.move[2] + " in vasul " + str(self.move[3])
            file.write(de_afis + "\n")

        for i in range(len(self.info)):
            file.write(str(i) + ": " + str(self.info[i][0]) + " " + str(self.info[i][1]) + " " + self.info[i][2] + "\n")

    # functia afisaeaza drumul cautat plecand de la un nod (self)
    # ca parametru primesc fisierul in care trebuie scris drumul
    # nu intoarce nimic
    def afisDrum(self, file):
        global max_in_memory
        global succ_generated
        global initial_time

        l = self.obtineDrum()

        duration = time.time() - initial_time
        cost = len(l) - 1

        file.write("Duration: " + str(duration) + "\n")
        file.write("Cost: " + str(cost) + "\n")
        file.write("Length: " + str(cost + 1) + " \n")
        file.write("Maximum nodes in memory: " + str(max_in_memory) + "\n")
        file.write("Generated successors: " + str(succ_generated) + "\n")
        file.write("Path:\n-------------------------------------\n")
        for i in range(len(l)):
            file.write(str(i + 1) + "\n")
            l[i].afisNode(file)

    def contineInDrum(self, infoNodNou):
        nodDrum = self
        while nodDrum is not None:
            if (infoNodNou == nodDrum.info):
                return True
            nodDrum = nodDrum.parinte

        return False


# din laborator. Sunt facute modificare pentru a se plia pe problema
class Graph:  # graful problemei
    def __init__(self, start, scope, transformation):
        self.start = start
        self.scope = scope
        self.transformations = transformation

    # primeste ca parametru un nod si verifica daca se afla in starea finala sau nu
    # returneaza true / false
    def testeaza_scop(self, nodCurent):
        used = set()  # sa nu numaram de 2 ori acelasi scop
        nMatches = 0  # numar de culori atinse

        for elem in nodCurent.info:
            culoare = elem[2]
            dimensiune = elem[1]
            # daca mai descoperim o culoare in plus nefolosita
            if culoare in self.scope.keys() and culoare not in used and dimensiune == self.scope[culoare]:
                used.add(culoare)
                nMatches += 1
        # daca am gasit toate culorile din scope
        if len(self.scope.keys()) == nMatches:
            return True
        return False

    # va genera succesorii sub forma de noduri in arborele de parcurgere
    def genereazaSuccesori(self, nodCurent, coada):
        listaSuccesori = []
        n = len(nodCurent.info)
        current_vessels = nodCurent.info

        for i in range(n):
            # daca nu e gol vasul din care turnam
            if current_vessels[i][1] > 0:
                # incercam sa facem toate combinatiile
                for j in range(n):
                    if i != j:
                        # daca nu e gol, putem pune si obtine o noua stare
                        if current_vessels[j][1] != current_vessels[j][0]:
                            # facem mutari
                            new_vessels = copy.deepcopy(current_vessels)
                            quantity = min(new_vessels[i][1], new_vessels[j][0] - new_vessels[j][1])
                            # noile cantitati si culori ce urmeaza sa fie puse
                            quantityi = new_vessels[i][1] - quantity
                            quantityj = new_vessels[j][1] + quantity
                            colorj = new_vessels[j][2]
                            colori = new_vessels[i][2]
                            # vedem ce culaore punem
                            if (new_vessels[i][2], new_vessels[j][2]) in self.transformations.keys():
                                colorj = self.transformations[(new_vessels[i][2], new_vessels[j][2])]
                            else:
                                # daca e gol pastreaza culoarea lui i
                                if new_vessels[j][1] == 0:
                                    colorj = new_vessels[i][2]
                                else:
                                    colorj = 'nedefinit'
                            # ii spunem ca nu are culoare daca e gol
                            if new_vessels[i][1] - quantity== 0:
                                colori = ""
                            new_vessels[i] = (new_vessels[i][0], quantityi, colori)
                            new_vessels[j] = (new_vessels[j][0], quantityj, colorj)

                            this_move = (i, quantity, current_vessels[i][2], j)

                            # bagam nodul in coada fara duplicate, adica daca am ajuns intr-un nod, ne intereseaza doar
                            # drumul cu costul cel mai mic pana la acel nod.
                            to_add = True

                            for k in range(len(coada)):
                                if coada[k].info == new_vessels:
                                    if coada[k].g <= nodCurent.g + 1:
                                        to_add = False
                                        break
                                    else:
                                        coada.pop(k)

                            # inseamna ca e ok sa il punem in lista de succesori
                            if to_add and not nodCurent.contineInDrum(new_vessels) and self.isWorthExpanding(
                                    new_vessels):
                                listaSuccesori.append(
                                    NodParcurgere(new_vessels, nodCurent.g + 1, nodCurent, move=this_move))
        return listaSuccesori

    # verifica daca poate avea solutie. modul in care face asta: Daca avem mai putine vase decat conditii
    # de final sau suma initiala de culori < suma target-urilor sau nu avem un vas suficient de mare inseamna ca nu
    # avem solutie
    def initialCheck(self, nodInitial):

        suma_culori = 0
        suma_target_culori = 0

        maxSize = 0
        maxTargetSize = 0
        # facem suma culorilor si maximul pentru scope
        for elem in self.scope.values():
            suma_target_culori += elem
            maxTargetSize = max(maxTargetSize, elem)
        # facem suma si maximul pentru array ul nostru initial
        for elem in nodInitial.info:
            suma_culori += elem[1]
            maxSize = max(maxSize, elem[0])
        # daca nu avem un vas suficient de mare sau suma culorilor initiale este mai mica decat suma culorilor din target
        if suma_culori < suma_target_culori or maxTargetSize > maxSize:
            return False
        # daca suma cantitatilor de culori < suma targe si daca avem loc sa punem pe cel mai voluminos, e ok
        return True

    # returneaza true daca mai are sens sa expandam nodul
    # primeste ca arugment nodul curent
    # verifica daca suma culorilor care nu sunt nedefinite >= suma target-urilor
    def isWorthExpanding(self, current_vessels):
        suma_culori = 0
        suma_target_culori = 0
        # calculam suma culorilor din starea finala
        for elem in self.scope.values():
            suma_target_culori += elem
        # calculam suma culorilor care nu sunt nedefinite din starea actuala
        for elem in current_vessels:
            if elem[2] != 'nedefinit':
                suma_culori += elem[1]

        if suma_culori < suma_target_culori:
            return False

        return True

    def __repr__(self):
        sir = ""
        for (k, v) in self.__dict__.items():
            sir += "{} = {}\n".format(k, v)
        return (sir)


##############################################################################################
#                                 Initializare problema                                      #
##############################################################################################		


# din laborator. Am adaugat in plus un argument de timeout
def uniform_cost(gr, nrSolutiiCautate=1, timeout=0.0, output_path=""):
    global max_in_memory
    global succ_generated
    global initial_time
    global output_name_bias
    initial_time = time.time()
    solCounter = 0

    # in coada vom avea doar noduri de tip NodParcurgere (nodurile din arborele de parcurgere)
    c = [NodParcurgere(gr.start, 0, None)]

    if not gr.initialCheck(c[0]):
        print("Nu are solutie. Iesim... \n")

    while len(c) > 0:
        current_time = time.time()
        if current_time - initial_time > timeout:
            print("Timeout")
            return

        nodCurent = c.pop(0)

        if gr.testeaza_scop(nodCurent):
            solCounter += 1
            file_path = open(output_path + "/Rezultat_" + str(solCounter) + output_name_bias + ".txt", "w")
            nodCurent.afisDrum(file_path)

            nrSolutiiCautate -= 1
            if nrSolutiiCautate == 0:
                return
        lSuccesori = gr.genereazaSuccesori(nodCurent, c)
        for s in lSuccesori:
            i = 0
            gasit_loc = False
            for i in range(len(c)):
                # ordonez dupa cost(notat cu g aici și în desenele de pe site)
                if c[i].g > s.g:
                    gasit_loc = True
                    break
            if gasit_loc:
                c.insert(i, s)
            else:
                c.append(s)
        succ_generated += len(lSuccesori)
        max_in_memory = max(max_in_memory, len(c))

    print("Nu s-au gasit suficiente solutii\n")


# functie de citire din fisierul de input
# returneaza trasnformariile posibile, lista initiala de vase si starea finala
# primeste ca input path-ul catre fisierul txt
def readInput(inputPath):
    # modul in care retinem starea initiala
    transformations = dict()
    vessels = []
	# modul in care retinem starea finala
    finalState = dict()

    file = open(inputPath, "r")
    lines = [x.strip() for x in file.readlines()]
    inputType = 0

	# citim din fisierul initial starea initiala, transformariile si starea finala
    for i in range(len(lines)):
        if lines[i] == 'stare_initiala':
            inputType = 1
            continue
        if lines[i] == 'stare_finala':
            inputType = 2
            continue
		# daca citim transformariile
        if inputType == 0:
            colors = lines[i].split()
            if (len(colors) != 3):
                print("Input invalid\n")
                return
            transformations[(colors[0], colors[1])] = colors[2]
            transformations[(colors[1], colors[0])] = colors[2]
		# daca citim starea initiala
        if inputType == 1:
            dim = lines[i].split()
            maxSize = int(dim[0])
            actualSize = int(dim[1])
            if actualSize == 0 and len(dim) == 3:
                print("Input invalid")
                return
            if actualSize != 0 and len(dim) == 2:
                print("Input invalid")
                return

            col = ""
            if actualSize == 0:
                col = ""
            else:
                col = dim[2]
            vessels.append((maxSize, actualSize, col))
		# daca citim starea finala
        if inputType == 2:
            ammount = int(lines[i].split()[0])
            col = lines[i].split()[1]
            finalState[col] = ammount

    return (transformations, vessels, finalState)


if __name__ == "__main__":
    inputFile = sys.argv[1]
    outputFolder = sys.argv[2]
    nrSol = int(sys.argv[3])
    timeout = float(sys.argv[4])

    transformations, vessels, finalState = readInput(inputFile)
    gr = Graph(vessels, finalState, transformations)

    output_name_bias = "_ucs_" + (inputFile.split(".")[0].split('/'))[1] + "_"

    uniform_cost(gr, nrSolutiiCautate=nrSol, timeout=timeout, output_path=outputFolder)