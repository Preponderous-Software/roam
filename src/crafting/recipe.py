# @author Copilot
# @since April 14th, 2026
class Recipe:
    def __init__(self, name, ingredients, resultClass, resultImagePath, resultCount=1):
        self.name = name
        self.ingredients = ingredients
        self.resultClass = resultClass
        self.resultImagePath = resultImagePath
        self.resultCount = resultCount

    def getName(self):
        return self.name

    def getIngredients(self):
        return self.ingredients

    def getResultClass(self):
        return self.resultClass

    def getResultCount(self):
        return self.resultCount

    def getResultImagePath(self):
        return self.resultImagePath

    def canCraft(self, inventory):
        for entityClass, requiredCount in self.ingredients.items():
            if inventory.getNumItemsByType(entityClass) < requiredCount:
                return False
        return True

    def craft(self, inventory):
        if not self.canCraft(inventory):
            return None

        for entityClass, requiredCount in self.ingredients.items():
            removed = 0
            for slot in inventory.getInventorySlots():
                if slot.isEmpty():
                    continue
                item = slot.getContents()[0]
                if isinstance(item, entityClass):
                    while removed < requiredCount and not slot.isEmpty():
                        contentItem = slot.getContents()[0]
                        if isinstance(contentItem, entityClass):
                            if slot.getNumItems() > 1:
                                slot.remove(contentItem)
                            else:
                                slot.clear()
                            removed += 1
                        else:
                            break
                if removed >= requiredCount:
                    break

        results = []
        for _ in range(self.resultCount):
            results.append(self.resultClass())
        return results
