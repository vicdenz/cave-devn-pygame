import json, sys, pygame
from pytmx.util_pygame import load_pygame
import random, math

# Initialise pygame
pygame.init()

# Set up the display
pygame.display.set_caption("Cave Devn")
width, height, unit = 20, 18, 32
screen = pygame.display.set_mode((width * unit, height * unit))

clock = pygame.time.Clock()
FPS = 60

#global assets
coinIcon = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/coin/coin_"+str(i+1)+".png"), (unit, unit)) for i in range(4)]
keyIcon = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/keys/keys_2_"+str(i+1)+".png"), (unit, unit)) for i in range(4)]
healthPotionIcon = pygame.image.load('assets/itemsImages/items/health-potion x32.png')
#coin/chest sounds
coinSound = [pygame.mixer.Sound("assets/sounds/coin/coin"+str(i+1)+".wav") for i in range(4)]
chestSound = [pygame.mixer.Sound("assets/sounds/boxOpen.wav")]
#attacking sounds (swing, hit)
axeSounds = [pygame.mixer.Sound("assets/sounds/combat/axeSwing.wav"), pygame.mixer.Sound("assets/sounds/combat/axeHit.wav")]
swordSounds = [pygame.mixer.Sound("assets/sounds/combat/swordSwing.wav"), pygame.mixer.Sound("assets/sounds/combat/swordHit.wav")]
daggerSounds = [pygame.mixer.Sound("assets/sounds/combat/daggerSwing.wav"), pygame.mixer.Sound("assets/sounds/combat/daggerHit.wav")]
#healing sounds
healSound = pygame.mixer.Sound("assets/sounds/heal.wav")
#equip sounds
equipSound = [pygame.mixer.Sound("assets/sounds/equip/equip"+str(i+1)+".wav") for i in range(3)]
#fade sound
fadeSound = pygame.mixer.Sound("assets/sounds/fade/fade.wav")

#load json weapons data
weaponsJson = open('assets/weapons.json')
weaponsData = json.load(weaponsJson)

# Class for the player
class Player(object):

    def __init__(self):
        #character properties
        self.name = 'Player'
        self.hitbox = pygame.Rect(spawns[0][0], spawns[0][1], 32, 32)
        self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/priests_idle/priest2/v1/priest2_v1_"+str(i+1)+".png"), (unit, unit)) for i in range(4)]
        self.left = False
        self.right = True
        self.spriteCount = 0
        self.coins = 0
        self.keys = 0
        self.walkSound = [pygame.mixer.Sound("assets/sounds/walk"+str(i+1)+".wav") for i in range(2)]

        #combat properties
        self.health = 20
        self.healthMax = 20
        self.speed = 4
        self.vel = [0, 0]

        # healing properties
        self.healing = False
        self.healthDelay = 0
        self.healthHealed = 10
        self.healthMaxDelay = 500

        # menu properties
        self.coinSpin = 0
        self.keySpin = 0

        # attack properties
        self.attacking = False
        self.attackTime = 0
        self.attackMaxTime = None
        self.equippedItem = 'unequipped'
        self.attackHitbox = {}
        self.isAttacked = False
        self.attackedDelay = 0
        self.attackedMaxDelay = 500
        self.enemyKilled = 0

        # inventory properties
        self.inventorySize = 6
        self.equippedSlot = 1
        self.inventory = ['unequipped' for slot in range(self.inventorySize)]
        # self.inventory = ['diamond dagger', 'diamond sword', 'diamond axe', 'health potion'] #(DEBUGING)
        # for slot in range(self.inventorySize-len(self.inventory)):
        #     self.inventory.append('unequipped')

    def move(self):
        # Move each axis separately. Note that this checks for collisions both times.
        if self.vel[0] != 0:
            if self.spriteCount % (FPS//2) == 0:
                self.walkSound[self.spriteCount//(FPS//2+1)].play()
            self.move_single_axis(self.vel[0], 0)
        if self.vel[1] != 0:
            if self.spriteCount % (FPS//2) == 0:
                self.walkSound[self.spriteCount//(FPS//2+1)].play()
            self.move_single_axis(0, self.vel[1])

    def move_single_axis(self, dx, dy):
        # Move the rect
        self.hitbox.left += dx
        self.hitbox.top += dy

        # If you collide with a wall/goal, move out based on velocity
        for wall in walls:
            if self.hitbox.colliderect(wall.hitbox):
                if dx > 0: # Moving right; Hit the left side of the wall
                    self.hitbox.right = wall.hitbox.left
                if dx < 0: # Moving left; Hit the right side of the wall
                    self.hitbox.left = wall.hitbox.right
                if dy > 0: # Moving down; Hit the top side of the wall
                    self.hitbox.bottom = wall.hitbox.top
                if dy < 0: # Moving up; Hit the bottom side of the wall
                    self.hitbox.top = wall.hitbox.bottom

        # If you collide with a coin, self.coins increase by value of coin and coins gets marked for deletion
        delete = []
        for coin in coins:
            if self.hitbox.colliderect(coin.hitbox):
                self.coins += coin.value
                delete.append(coins.index(coin))
                coinSound[random.randint(0, len(coinSound)-1)].play()
        for index in delete:
            coins.pop(index)
        
        # If you collide with a unlocked chest, self.keys increase by 1. If you collide with a locked chest, you get a random amount of coins or a random item.
        delete = []
        for chest in chests:
            if chest.locked:
                if self.keys > 0:
                    for wall in walls:
                        try:
                            if type(wall.locked) == bool:
                                walls.remove(wall)
                        except AttributeError:
                            pass
                    if self.hitbox.colliderect(chest.hitbox):
                        self.keys -= 1
                        weaponRandom = random.randint(1, 100)#60% for bronze, 30% for steel, 10% for diamond
                        if weaponRandom <= 60:
                            weaponRandom = 0
                        elif weaponRandom <= 90:
                            weaponRandom = 1
                        else:
                            weaponRandom = 2
                        weaponRarity = list(weaponsData)[weaponRandom]
                        weaponType = list(weaponsData[weaponRarity])[random.randint(0, len(weaponsData[weaponRarity])-1)]
                        # newWeapon = weaponsData[weaponRarity][weaponType]
                        equipSound[random.randint(0, len(equipSound)-1)].play()

                        for i, slot in enumerate(self.inventory):
                            if slot == 'unequipped':
                                self.inventory[i] = str(weaponRarity+' '+weaponType)
                                break
                            elif i+1 == self.inventorySize:
                                newCoins = random.randint(2, 4)
                                self.coins += random.randint(2, 4)
                                coinSound[random.randint(0, len(coinSound)-1)].play()
                                texts.append(textDisplay(player.hitbox.x, player.hitbox.y, '+'+str(newCoins), (255, 235, 50)))
                                break

                        if len(self.inventory) == self.inventorySize:
                            for i, slot in enumerate(self.inventory):
                                if slot == 'unequipped':
                                    if random.randint(1, 100) <= 50:#if true, give health potion, 50% chance
                                        self.inventory[i] = 'health potion'
                                    else:
                                        newCoins = random.randint(2, 4)
                                        self.coins += newCoins
                                        coinSound[random.randint(0, len(coinSound)-1)].play()
                                        texts.append(textDisplay(player.hitbox.x, player.hitbox.y, '+'+str(newCoins), (255, 235, 50)))
                                    break
                        delete.append(chests.index(chest))
                else:
                    if chest not in walls:
                        walls.append(chest)
            else:
                if self.hitbox.colliderect(chest.hitbox):
                    self.keys += 1
                    delete.append(chests.index(chest))
                    chestSound[random.randint(0, len(chestSound)-1)].play()
        for index in delete:
            chests.pop(index)

    def heal(self):
        if not self.health + 1 > self.healthMax:
            self.health += 1

    def drawMenu(self):
        #main border
        pygame.draw.rect(screen, (61, 37, 59), pygame.Rect(0, 16 * unit, width * unit, 3 * unit), 4, 10)
        
        #draw player icon and main border
        screen.blit(pygame.transform.scale(self.sprite[0], (2 * unit, 2 * unit)), (0, 16 * unit))
        pygame.draw.rect(screen, (61, 37, 59), pygame.Rect(0, 16 * unit, 2 * unit, 3 * unit), 4, 10)

        #draw # of coins
        coinCount = displayFont.render(str(self.coins), False, (255, 213, 105))
        if self.coinSpin + 1 >= FPS:
            self.coinSpin = 0

        screen.blit(coinIcon[self.coinSpin//(FPS//4)], (2 * unit, 16 * unit))
        self.coinSpin += 1

        screen.blit(coinCount, (3 * unit, 16 * unit + 7))

        #draw # of keys
        keyCount = displayFont.render(str(self.keys), False, (173, 193, 207))
        if self.keySpin + 1 >= FPS:
            self.keySpin = 0

        screen.blit(keyIcon[self.keySpin//(FPS//4)], (2 * unit, 17 * unit))
        self.keySpin += 1

        screen.blit(keyCount, (3 * unit, 17 * unit + 7))

        #properties border
        pygame.draw.rect(screen, (61, 37, 59), pygame.Rect(2 * unit - 4, 16 * unit, 2 * unit, 3 * unit), 4, 10)

        #draw inventory grid
        pygame.draw.line(screen, (61, 37, 59), (4 * unit - 8, 17 * unit + 1), ((4 + self.inventorySize) * unit - 10, 17 * unit + 1), 4)#cover holes
        for h in range(self.inventorySize // 3):
            for w in range(self.inventorySize // 2):
                if h*3+(w+1) == self.equippedSlot:
                    equippedPos = [w, h]
                slotPos = pygame.Rect((4 + w*2) * unit - 8, (16 + h) * unit, 2 * unit + 4, 1 * unit + 4)
                pygame.draw.rect(screen, (61, 37, 59), slotPos, 4, 10)
                if self.inventory[h*3+w] != 'unequipped':
                    slotData = self.inventory[h*3+w].split(' ')
                    if self.inventory[h*3+w] == 'health potion':
                        slotRect = healthPotionIcon.get_rect()
                        slotRect.center = slotPos.center
                        screen.blit(healthPotionIcon, slotRect)
                    else:
                        slotData = self.inventory[h*3+w].split(' ')
                        slotImage = pygame.transform.rotate(pygame.image.load(weaponsData[slotData[0]][slotData[1]]['image']+' x3.png'), -90)
                        slotRect = slotImage.get_rect()
                        slotRect.center = slotPos.center
                        screen.blit(slotImage, slotRect)

        #draw equipped slot
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect((4 + equippedPos[0]*2) * unit - 8, (16 + equippedPos[1]) * unit, 2 * unit + 4, 1 * unit + 4), 4, 10)

    def drawHealth(self):
        pygame.draw.line(screen, (0, 255, 0), (self.hitbox.x, self.hitbox.y - 4), (self.hitbox.x + (self.health/self.healthMax)*unit - 1, self.hitbox.y - 4), 4)

    def draw(self):
        if self.spriteCount + 1 > FPS:
            self.spriteCount = 0

        if self.left:
            screen.blit(pygame.transform.flip(self.sprite[self.spriteCount//(FPS//4)], True, False), self.hitbox)
        elif self.right:
            screen.blit(self.sprite[self.spriteCount//(FPS//4)], self.hitbox)
        self.spriteCount += 1

        if self.inventory[self.equippedSlot-1] != 'unequipped':
            if self.attacking == False and self.healing == False:
                if self.inventory[self.equippedSlot-1] == 'health potion':
                    slotImage = healthPotionIcon
                    slotRect = slotImage.get_rect()
                    if self.left:
                        slotRect.x, slotRect.bottom = self.hitbox.x - 7, self.hitbox.bottom + 6 - self.spriteCount//(30-1)
                        screen.blit(pygame.transform.flip(slotImage, True, False), slotRect)
                    elif self.right:
                        slotRect.x, slotRect.bottom = self.hitbox.right - slotRect.width + 7, self.hitbox.bottom + 6 - self.spriteCount//(30-1)
                        screen.blit(slotImage, slotRect)
                else:
                    slotData = self.inventory[self.equippedSlot-1].split(' ')
                    slotImage = pygame.image.load(weaponsData[slotData[0]][slotData[1]]['image']+' x2.png')
                    slotRect = slotImage.get_rect()
                    if self.left:
                        slotRect.x, slotRect.bottom = self.hitbox.x - 2, self.hitbox.bottom - 8 - self.spriteCount//(30-1)
                        screen.blit(pygame.transform.flip(slotImage, True, False), slotRect)
                    elif self.right:
                        slotRect.x, slotRect.bottom = self.hitbox.right - slotRect.width + 2, self.hitbox.bottom - 8 - self.spriteCount//(30-1)
                        screen.blit(slotImage, slotRect)
            else:
                equippedSlotData = self.equippedItem.split(' ')
                if self.healing:
                    image, rect, offset, pivot = animateWeapon(self, equippedSlotData, healthPotionIcon)
                    screen.blit(image, rect)
                    # pygame.draw.circle(screen, (30, 250, 70), pivot, 2)#pivot green
                    # pygame.draw.circle(screen, (250, 30, 70), pivot + offset, 2)#offset red
                    # pygame.draw.rect(screen, (255, 255, 255), rect, 1) #DEBUGGING
                else:
                    attackSlotImage = pygame.image.load(weaponsData[equippedSlotData[0]][equippedSlotData[1]]['image']+' x2.png')
                    if equippedSlotData[1] == 'dagger':
                        rect, image = animateWeapon(self, equippedSlotData, attackSlotImage)
                        screen.blit(image, rect)
                        # pygame.draw.rect(screen, (255, 255, 255), rect, 1) #DEBUGGING
                    else:
                        image, rect, offset, pivot = animateWeapon(self, equippedSlotData, attackSlotImage)

                        screen.blit(image, rect)
                        # pygame.draw.circle(screen, (30, 250, 70), pivot, 2)#pivot green
                        # pygame.draw.circle(screen, (250, 30, 70), pivot + offset, 2)#offset red
                        # pygame.draw.rect(screen, (255, 255, 255), rect, 1) #DEBUGGING

        self.drawMenu()

class Vampire(object):
    def __init__(self, x, y, boss=False):
        self.name = 'Vampire'
        self.hitbox = pygame.Rect(x * unit, y * unit, unit*(int(boss)+1), unit*(int(boss)+1))
        self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/monsters_idle/vampire/v2/vampire_v2_"+str(i+1)+".png"), self.hitbox.size) for i in range(4)]
        self.spriteCount = 0
        self.left = False
        self.right = True

        # combat data
        self.isAttacked = False
        self.health = 10*(int(boss)*0.5+1)
        self.healthMax = 10*(int(boss)*0.5+1)
        self.damage = 2*(int(boss)*0.5+1)
        self.attacking = False
        self.attackTime = 0
        self.attackMaxTime = 500*(int(boss)+1)
        self.equippedItem = 'vampire dagger'
        self.attackHitbox = {}

        # movement data
        self.speed = 3
        self.vel = 0
        self.attackLocation = None
        self.attackDelay = 0
        self.attackMaxDelay = 500*(int(boss)*0.5+1)

    def move(self):
        rectDistance = pygame.math.Vector2(player.hitbox.center) - pygame.math.Vector2(self.hitbox.center)
        linearDistance = findDistance(rectDistance[0], rectDistance[1])
        if linearDistance < (self.hitbox.width//2 + self.hitbox.width):
            if abs(rectDistance[0]) == rectDistance[0]:
                self.left = False
                self.right = True
            else:
                self.left = True
                self.right = False
            if not self.attacking and int(linearDistance) == 0:
                bounce = findWallPath(self, [self.speed*2, self.speed*2])
                self.move_single_axis(bounce[0], bounce[1])
            elif not self.attacking and random.randint(1, FPS*2) == 1:
                self.attacking = True
                self.attackLocation = player.hitbox.center
            else:
                self.vel = self.speed
        else:
            self.vel = 0

        if self.attacking:
            if self.attackDelay >= self.attackMaxDelay:
                self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/monsters_idle/vampire/v2/vampire_v2_"+str(i+1)+".png"), self.hitbox.size) for i in range(4)]
                attackRectDistance = pygame.math.Vector2(self.attackLocation) - pygame.math.Vector2(self.hitbox.center)

                if abs(attackRectDistance[0]) == attackRectDistance[0]:
                    self.left = False
                    self.right = True
                else:
                    self.left = True
                    self.right = False
                if not abs(sum(attackRectDistance)) <= player.speed*2:
                    bounce = [player.speed, player.speed]
                    for index, position in enumerate(attackRectDistance):
                        if abs(self.attackLocation[index] - self.hitbox.center[index]) <= player.speed:
                            bounce[index] = 0
                        elif abs(position) != position:
                            bounce[index] = -bounce[index]
                    self.move_single_axis(bounce[0], bounce[1])
                else:
                    self.attacking = False
                    self.attackHitbox.clear()
                    self.attackLocation = None
                    self.attackDelay = 0
            else:
                self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/monsters_idle/vampire/v1/vampire_v1_"+str(i+1)+".png"), self.hitbox.size) for i in range(4)]
                self.attackDelay += 1000/FPS
        else:
            if abs(rectDistance[0]) == rectDistance[0]:
                self.move_single_axis(-self.vel, 0)
            if abs(rectDistance[0]) != rectDistance[0]:
                self.move_single_axis(self.vel, 0)
            if abs(rectDistance[1]) == rectDistance[1]:
                self.move_single_axis(0, -self.vel)
            if abs(rectDistance[1]) != rectDistance[1]:
                self.move_single_axis(0, self.vel)

    def move_single_axis(self, dx, dy):
        # Move the rect
        self.hitbox.x += dx
        self.hitbox.y += dy

        for wall in walls:
            if self.hitbox.colliderect(wall.hitbox):
                if dx > 0: # Moving right; Hit the left side of the wall
                    self.hitbox.right = wall.hitbox.left
                if dx < 0: # Moving left; Hit the right side of the wall
                    self.hitbox.left = wall.hitbox.right
                if dy > 0: # Moving down; Hit the top side of the wall
                    self.hitbox.bottom = wall.hitbox.top
                if dy < 0: # Moving up; Hit the bottom side of the wall
                    self.hitbox.top = wall.hitbox.bottom
        for enemy in enemies[current_level-1]:
            if enemy != self:
                if self.hitbox.colliderect(enemy.hitbox):
                    if dx > 0: # Moving right; Hit the left side of the wall
                        self.hitbox.right = enemy.hitbox.left
                    if dx < 0: # Moving left; Hit the right side of the wall
                        self.hitbox.left = enemy.hitbox.right
                    if dy > 0: # Moving down; Hit the top side of the wall
                        self.hitbox.bottom = enemy.hitbox.top
                    if dy < 0: # Moving up; Hit the bottom side of the wall
                        self.hitbox.top = enemy.hitbox.bottom

    def drawHealth(self):
        pygame.draw.line(screen, (0, 255, 0), (self.hitbox.x, self.hitbox.y - 4), (self.hitbox.x + (self.health/self.healthMax)*self.hitbox.width - 1, self.hitbox.y - 4), 4)

    def draw(self):
        if self.spriteCount + 1 > FPS:
            self.spriteCount = 0

        if self.left:
            screen.blit(pygame.transform.flip(self.sprite[self.spriteCount//(FPS//4)], True, False), self.hitbox)
        elif self.right:
            screen.blit(self.sprite[self.spriteCount//(FPS//4)], self.hitbox)
        self.spriteCount += 1

        if self.attacking == False:
            weaponData = self.equippedItem.split(' ')
            weaponImage = pygame.image.load('assets/itemsImages/weapons/enemy/'+weaponData[0]+'-'+weaponData[1]+' x4.png')
            weaponRect = weaponImage.get_rect()
            if self.left:
                weaponRect.x, weaponRect.bottom = self.hitbox.x - 2, self.hitbox.bottom - 8 - self.spriteCount//(FPS//2-1)
                screen.blit(pygame.transform.flip(weaponImage, True, False), weaponRect)
            elif self.right:
                weaponRect.x, weaponRect.bottom = self.hitbox.x + self.hitbox.width - weaponRect.width + 2, self.hitbox.bottom - 8 - self.spriteCount//(FPS//2-1)
                screen.blit(weaponImage, weaponRect)
        else:
            equippedItemData = self.equippedItem.split(' ')
            equippedItemImage = pygame.image.load('assets/itemsImages/weapons/enemy/'+equippedItemData[0]+'-'+equippedItemData[1]+' x4.png')
            if equippedItemData[1] == 'dagger':
                rect, image = animateWeapon(self, equippedItemData, equippedItemImage)
                screen.blit(image, rect)
            else:
                image, rect, offset = animateWeapon(self, equippedItemData, equippedItemImage)

                screen.blit(image, rect)
                # pygame.draw.circle(screen, (30, 250, 70), pivot, 2)#pivot green (DEBUG)
                # pygame.draw.circle(screen, (250, 30, 70), pivot + rotatedOffset, 2)#offset red
                # pygame.draw.rect(screen, (255, 255, 255), rect, 1) #DEBUGGING

class Skull(object):
    def __init__(self, x, y, boss=False):
        self.name = 'Skull'
        self.hitbox = pygame.Rect(x * unit, y * unit, unit*(int(boss)+1), unit*(int(boss)+1))
        self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/monsters_idle/skull/v2/skull_v2_"+str(i+1)+".png"), self.hitbox.size) for i in range(4)]
        # self.projectileImage = pygame.image.load("assets/itemsImages/weapons/enemy/flame-skull x"+str(16*(int(boss)+1))+".png")
        self.projectileImage = pygame.image.load("assets/itemsImages/weapons/enemy/flame-skull x32.png")
        self.spriteCount = 0
        self.left = False
        self.right = True

        # combat data
        self.isAttacked = False
        self.health = 7*(int(boss)*0.5+1)
        self.healthMax = 7*(int(boss)*0.5+1)
        self.damage = 2*(int(boss)*0.5+1)
        self.attacking = False
        self.attackTime = 0
        self.attackMaxTime = 700*(int(boss)+1)
        self.attackHitbox = []
        self.projectileSpeed = 6

        # movement data
        self.speed = 2
        self.vel = 0
        self.attackDelay = 0
        self.attackMaxDelay = 800*(int(boss)*0.5+1)

    def move(self):
        rectDistance = pygame.math.Vector2(player.hitbox.center) - pygame.math.Vector2(self.hitbox.center)
        linearDistance = findDistance(rectDistance[0], rectDistance[1])
        if linearDistance < self.hitbox.width*8:
            if not self.attacking and random.randint(1, FPS) == 1:
                self.attacking = True
        if linearDistance < self.hitbox.width*2:
            if abs(rectDistance[0]) == rectDistance[0]:
                self.left = False
                self.right = True
            else:
                self.left = True
                self.right = False
            if not self.attacking:
                if int(linearDistance) == 0:
                    bounce = findWallPath(self, [self.speed*2, self.speed*2])
                    self.move_single_axis(bounce[0], bounce[1])
                else:
                    self.vel = self.speed
        else:
            self.vel = 0

        if self.attacking:
            if self.attackDelay >= self.attackMaxDelay:
                self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/monsters_idle/skull/v2/skull_v2_"+str(i+1)+".png"), self.hitbox.size) for i in range(4)]
                projectileVel = [rectDistance[0]*(self.projectileSpeed/linearDistance), rectDistance[1]*(self.projectileSpeed/linearDistance)]
                newProjectile = pygame.Rect(self.hitbox.center[0], self.hitbox.center[1], unit, unit)
                self.attackHitbox.append([newProjectile, projectileVel])

                self.attacking = False
                self.attackDelay = 0
            else:
                self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/monsters_idle/skull/v1/skull_v1_"+str(i+1)+".png"), self.hitbox.size) for i in range(4)]
                self.attackDelay += 1000/FPS
        else:
            if abs(rectDistance[0]) == rectDistance[0]:
                self.move_single_axis(-self.vel, 0)
            if abs(rectDistance[0]) != rectDistance[0]:
                self.move_single_axis(self.vel, 0)
            if abs(rectDistance[1]) == rectDistance[1]:
                self.move_single_axis(0, -self.vel)
            if abs(rectDistance[1]) != rectDistance[1]:
                self.move_single_axis(0, self.vel)

    def move_single_axis(self, dx, dy):
        # Move the rect
        self.hitbox.x += dx
        self.hitbox.y += dy

        for wall in walls + enemies[current_level-1]:
            if wall != self:
                if self.hitbox.colliderect(wall.hitbox):
                    if dx > 0: # Moving right; Hit the left side of the wall
                        self.hitbox.right = wall.hitbox.left
                    if dx < 0: # Moving left; Hit the right side of the wall
                        self.hitbox.left = wall.hitbox.right
                    if dy > 0: # Moving down; Hit the top side of the wall
                        self.hitbox.bottom = wall.hitbox.top
                    if dy < 0: # Moving up; Hit the bottom side of the wall
                        self.hitbox.top = wall.hitbox.bottom

    def moveProjectile(self, index):
        projectileHitbox = self.attackHitbox[index][0]
        projectileVel = self.attackHitbox[index][1]

        for wall in walls + enemies[current_level-1]:
            if wall != self:
                if projectileHitbox.colliderect(wall.hitbox):
                    self.attackHitbox.pop(index)
                    return

        projectilePos = pygame.Vector2(projectileHitbox.center)
        projectileHitbox.center = projectilePos + projectileVel

    def drawHealth(self):
        pygame.draw.line(screen, (0, 255, 0), (self.hitbox.x, self.hitbox.y - 4), (self.hitbox.x + (self.health/self.healthMax)*self.hitbox.width - 1, self.hitbox.y - 4), 4)

    def draw(self):
        if self.spriteCount + 1 > FPS:
            self.spriteCount = 0

        if self.left:
            screen.blit(pygame.transform.flip(self.sprite[self.spriteCount//(FPS//4)], True, False), self.hitbox)
        elif self.right:
            screen.blit(self.sprite[self.spriteCount//(FPS//4)], self.hitbox)
        self.spriteCount += 1

        # for hitbox in self.attackHitbox: #DEBUGGING
        #     pygame.draw.rect(screen, (255, 255, 255), hitbox[0], 1)

class Goal(object):
    def __init__(self, x, y, image):
        self.hitbox = pygame.Rect(x * unit, y * unit, unit, unit)
        self.sprite = pygame.transform.scale(image, (unit, unit))

    def draw(self):
        screen.blit(self.sprite, self.hitbox)

class Wall(object):
    def __init__(self, x, y, image):
        self.hitbox = pygame.Rect(x * unit, y * unit, unit, unit)
        self.sprite = pygame.transform.scale(image, (unit, unit))
    
    def draw(self):
        screen.blit(self.sprite, self.hitbox)

class Coin(object):
    def __init__(self, x, y, value):
        self.hitbox = pygame.Rect(x * unit, y * unit, unit, unit)
        self.spriteCount = 0
        self.value = value
    
    def draw(self):
        if self.spriteCount + 1 > FPS:
            self.spriteCount = 0

        screen.blit(coinIcon[self.spriteCount//(FPS//4)], self.hitbox)
        self.spriteCount += 1

class Chest(object):
    def __init__(self, x, y, image, locked):
        self.hitbox = pygame.Rect(x * unit, y * unit, unit, unit)
        self.sprite = [pygame.transform.scale(img, (unit, unit)) for img in image]
        self.spriteCount = 0
        self.locked = locked
    
    def draw(self):
        if self.spriteCount + 1 > FPS:
            self.spriteCount = 0

        screen.blit(self.sprite[self.spriteCount//(FPS//4)], self.hitbox)
        self.spriteCount += 1

class Fire(object):
    def __init__(self, x, y, image, flameOffset, flameRadius, flameDifference):
        self.hitbox = pygame.Rect(x * unit, y * unit, unit, unit)
        self.sprite = [pygame.transform.scale(img, (unit, unit)) for img in image]
        self.flamePoint = [(x + flameOffset[0], y + flameOffset[1]), flameRadius, [flameRadius-flameDifference//2, flameRadius+flameDifference//2], True]
        self.flameSpeed = 0.005
        self.spriteCount = 0

    def draw(self):
        if self.spriteCount + 1 > FPS:
            self.spriteCount = 0

        screen.blit(self.sprite[self.spriteCount//(FPS//4)], self.hitbox)
        self.spriteCount += 1

        if self.flamePoint[3]:
            if self.flamePoint[1] * (1 + self.flameSpeed) <= self.flamePoint[2][1]:
                self.flamePoint[1] *= (1 + self.flameSpeed)
            else:
                self.flamePoint[3] = False
        else:
            if self.flamePoint[1] * (1 - self.flameSpeed) >= self.flamePoint[2][0]:
                self.flamePoint[1] *= (1 - self.flameSpeed)
            else:
                self.flamePoint[3] = True

        # radiusInner = int(self.flamePoint[1])
        # screen.blit(circleToAlpha(radiusInner, (255, 190, 60), 100), ((self.flamePoint[0][0])*unit - radiusInner, (self.flamePoint[0][1])*unit - radiusInner))

        radiusOuter = int(self.flamePoint[1] * 2)
        screen.blit(circleToAlpha(radiusOuter, (255, 140, 40), 70), ((self.flamePoint[0][0])*unit - radiusOuter, (self.flamePoint[0][1])*unit - radiusOuter))

class Arrow(object):
    def __init__(self, x, y):
        self.hitbox = pygame.Rect(x * unit, y * unit - 8, unit, unit)
        self.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/interface/arrow_"+str(i+1)+".png"), (unit, unit)) for i in range(4)]
        self.spriteCount = 0
    
    def draw(self):
        if self.spriteCount + 1 > FPS:
            self.spriteCount = 0

        screen.blit(self.sprite[self.spriteCount//(FPS//4)], self.hitbox)
        self.spriteCount += 1

class textDisplay(object):
    def __init__(self, x, y, text, color):
        self.pos = [x, y]
        self.textSurface = displayFont.render(text, False, color)
        self.alpha = 300

    def fade(self):
        if self.alpha <= 0:
            texts.remove(self)
        else:
            self.textSurface.set_alpha(self.alpha)
            self.alpha -= 4

    def draw(self):
        screen.blit(self.textSurface, self.pos)
        self.fade()

def rotateSurface(image, angle, pivot, offset):
    #image= Surface, angle= float, pivot= image.center, offset= math.Vector2
    rotatedImage = pygame.transform.rotozoom(image, -angle, 1) #rotate clockwise
    rotatedOffset = offset.rotate(angle)
    rect = rotatedImage.get_rect(center=pivot+rotatedOffset)
    return rotatedImage, rect, rotatedOffset

def calculatePosition(direction, vel):
    for index, position in enumerate(direction):
        if abs(position) != position:
            vel[index] = -vel[index]
    return vel

def findWallPath(character, bounce):
    # character = enemy/player class
    # bounce = speed of move
    wallLocation = [wall.hitbox for wall in walls]
    for w in range(character.hitbox.x - character.hitbox.width, character.hitbox.x + character.hitbox.height*2, unit):
        # bounced = False
        for h in range(character.hitbox.y - character.hitbox.width, character.hitbox.y + character.hitbox.height*2, unit):
            if w != player.hitbox.x:
                if h != player.hitbox.y:
                    try:
                        walls[wallLocation.index(pygame.Rect(w, h, unit, unit))]
                    except ValueError:
                        bounceRectDistance = pygame.math.Vector2(w, h) - pygame.math.Vector2(character.hitbox.x, character.hitbox.y)
                        bounce = calculatePosition(bounceRectDistance, bounce)
                        return bounce

def animateWeapon(character, data, image):
    if data[1] == 'dagger':
        image = pygame.transform.rotate(image, -90)
        if character.attackMaxTime - character.attackTime <= character.attackMaxTime//2:
            depth = (12 * ((character.attackMaxTime - character.attackTime)/1000)) * 2
        else:
            depth = (12 * (character.attackTime/1000)) * 2
        rect = image.get_rect()
        if character.left:
            rect.x, rect.bottom = character.hitbox.x - rect.width + 12 - depth, character.hitbox.bottom - 8 - character.spriteCount//(FPS//2-1)
            image = pygame.transform.flip(image, True, False)
        elif character.right:
            rect.x, rect.bottom = character.hitbox.x + character.hitbox.width - 12 + depth, character.hitbox.bottom - 8 - character.spriteCount//(FPS//2-1)
            screen.blit(image, rect)
        character.attackHitbox[character.equippedItem] = rect#add weapon hitbox to attack hitbox dictionary
        return rect, image
    elif data[0] == 'health':
        offset = pygame.math.Vector2(0, 9)
        if character.left:
            pivot = pygame.math.Vector2(character.hitbox.x + 7, character.hitbox.y + 13 - character.spriteCount//(30-1))
            angle = (90 * (character.healthDelay/character.healthMaxDelay))
            image = pygame.transform.flip(image, True, False)
        elif character.right:
            pivot = pygame.math.Vector2(character.hitbox.right - 7, character.hitbox.y + 13 - character.spriteCount//(30-1))
            angle = -(90 * (character.healthDelay/character.healthMaxDelay))
        rotatedImage, rotatedRect, rotatedOffset = rotateSurface(image, angle, pivot, offset)
        character.attackHitbox[character.equippedItem] = rotatedRect#add weapon hitbox to attack hitbox dictionary
        return rotatedImage, rotatedRect, rotatedOffset, pivot
    else:
        offset = pygame.math.Vector2(2, -12)
        if character.left:
            pivot = pygame.math.Vector2(character.hitbox.x + 6, character.hitbox.y + 18 - character.spriteCount//(30-1))
            angle = -(90 * (character.attackTime/character.attackMaxTime))
            image = pygame.transform.flip(image, True, False)
        elif character.right:
            pivot = pygame.math.Vector2(character.hitbox.right - 6, character.hitbox.y + 18 - character.spriteCount//(30-1))
            angle = (90 * (character.attackTime/character.attackMaxTime))
        rotatedImage, rotatedRect, rotatedOffset = rotateSurface(image, angle, pivot, offset)
        character.attackHitbox[character.equippedItem] = rotatedRect#add weapon hitbox to attack hitbox dictionary
        return rotatedImage, rotatedRect, rotatedOffset, pivot

goals = [] # List to hold goals
walls = [] # List to hold walls
coins = [] # List to hold coins
chests = [] # List to hold chests
flames = [] # List to hold fire sources
arrows = [] # List to hold arrows P.O.Is
texts = [] # List to hold text displays
spawns = [[304, 32], [32, 448], [288, 448]]
goalZone = [pygame.Rect(32, 416, 64, 64), pygame.Rect(256, 0, 128, 64), pygame.Rect(256, 0, 128, 64)]
goalPass = False
goalLastPass = goalPass
arrowPos = [[1, 14], [9.5, 0], [9.5, 0]]
max_level = 3 # Max level
current_level = 1 # Hold the current level
last_level = current_level
tmxdata = load_pygame("maps\level"+str(current_level)+".tmx")
player = Player() # Create the player
enemies = [[], [], [Vampire(7, 5, True), Skull(10, 5, False)]]
displayFont = pygame.font.Font('assets/PixelFJVerdana.ttf', 8)
# Holds the level layout in a list of strings.
#levels = [["WWWWWWWWWWWWWWWWWWWW", "W   S              W", "W         WWWWWW   W", "W   WWWW       W   W", "W   W        WWWW  W", "W WWW  WWWW        W", "W   W     W W      W", "W   W     W   WWW WW", "W   WWW WWW   W W  W", "W     W   W   W W  W", "WWW   W   WWWWW W  W", "W W      WW        W", "W W   WWWW   WWW   W", "W     W    E   W   W", "WWWWWWWWWWWWWWWWWWWW",],["WWWWWWWWWWWWWWWWWWWW", "WE             W   W", "WW WW      WWWWW   W", "W   WWWWWW W       W", "W              WW  W", "WWW WWWW           W", "W   W     WWWW WWWWW", "W   W WW       W   W", "W   WWW  W         W", "W     W       WW   W", "W     WWWW  WWW    W", "W           W      W", "W    WWW    WWWW   W", "W      W   S       W", "WWWWWWWWWWWWWWWWWWWW",]]

def blit_noCollide_tile(tmxdata):
    for i, layer in enumerate(tmxdata):
        if layer.name == "Decor" or layer.name == "Floor":
            for tile in layer.tiles():
                # tile = [x grid location, y grid location, image data for blitting]
                x = tile[0]
                y = tile[1]
                screen.blit(pygame.transform.scale(tile[2], (unit, unit)), (x * unit, y * unit))

def parse(tmxdata):
    # Parse the tmxdata file. if collision = True, add rect at position to walls list. find goal position and assign.
    walls.clear()
    goals.clear()
    coins.clear()
    chests.clear()
    flames.clear()

    for i, layer in enumerate(tmxdata):
        for tile in layer.tiles():
            if current_level == 3:
                if goalPass:
                    if layer.name == 'Door Closed':
                        break
                else:
                    if layer.name == 'Door Open':
                        break
            else:
                if layer.visible == False:
                    break
            # tile =  [x grid location, y grid location, image data for blitting]
            x, y, image = tile[0], tile[1], tile[2]
            properties = tmxdata.get_tile_properties(x, y, i)

            if properties['collision']:
                walls.append(Wall(x, y, image))
            if properties['goal']:
                goals.append(Goal(x, y, image))
                walls.append(Wall(x, y, image))
            if properties['coin']:
                coins.append(Coin(x, y, 1))
            if properties['torch']:
                flames.append(Fire(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/torch/torch_"+str(i+1)+".png") for i in range(4)], [0.5, 0.6], 7, 5))
            elif properties['side-torch']:
                flames.append(Fire(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/torch/side_torch_"+str(i+1)+".png") for i in range(4)], [0.3, 0.5], 7, 5))
            elif properties['candle']:
                flames.append(Fire(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/torch/candlestick_2_"+str(i+1)+".png") for i in range(4)], [0.5, 0.5], 9, 6))
            elif properties['small-candle']:
                flames.append(Fire(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/torch/candlestick_1_"+str(i+1)+".png") for i in range(4)], [0.5, 0.5], 9, 6))
            if properties['chest']:
                if properties['box']:
                    chests.append(Chest(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/box_2/box_2_"+str(i+1)+".png") for i in range(4)], properties['locked']))
                elif properties['miniBox']:
                    chests.append(Chest(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/mini_box_2/mini_box_2_"+str(i+1)+".png") for i in range(4)], properties['locked']))
                elif properties['lockedBox']:
                    chests.append(Chest(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/box_1/box_1_"+str(i+1)+".png") for i in range(4)], properties['locked']))
                elif properties['lockedMiniBox']:
                    chests.append(Chest(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/mini_box_1/mini_box_1_"+str(i+1)+".png") for i in range(4)], properties['locked']))
                elif properties['lockedChest']:
                    chests.append(Chest(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/chest/chest_"+str(i+1)+".png") for i in range(4)], properties['locked']))
                elif properties['lockedMiniChest']:
                    chests.append(Chest(x, y, [pygame.image.load("assets/2D Pixel Dungeon Asset Pack/items and trap_animation/mini_chest/mini_chest_"+str(i+1)+".png") for i in range(4)], properties['locked']))
    return goals

# pythagorean theorem to find length 'c'
def findDistance(a, b):
    return math.sqrt(a**2 + b**2)

def circleToAlpha(radius, color, alpha):
  circleSurf = pygame.Surface((radius * 2, radius * 2))
  circleSurf.set_alpha(alpha)
  circleSurf.set_colorkey((0, 0, 0))
  pygame.draw.circle(circleSurf, color, (radius, radius), radius)

  return circleSurf

def fade(width, height, start, end, step):
    fade = pygame.Surface((width, height))
    fade.fill((0, 0, 0))
    for alpha in range(start, end, step):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        fade.set_alpha(alpha)

        redrawGameWindow()

        screen.blit(fade, (0, 0))

        pygame.display.update()
        pygame.time.delay(5)

def displayMessage(width, height, messages, color):
    fade = pygame.Surface((width, height))
    messagesText = [displayFont.render(message.upper(), False, color) for message in messages]
    screenRect = screen.get_rect()

    fade.fill((0, 0, 0))
    for alpha in range(300):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        fade.set_alpha(alpha)

        redrawGameWindow()

        screen.blit(fade, (0, 0))
        for i, message in enumerate(messagesText):
            messageRect = message.get_rect(center=screenRect.center)
            screen.blit(message, [messageRect[0], messageRect[1]+i*messageRect.height])

        pygame.display.update()
        pygame.time.delay(5)
    pygame.quit()
    sys.exit()

def redrawGameWindow():
    global angle
    screen.fill((37, 19, 26))
    # items drawn last are on top of items drawn first
    for wall in walls:
        wall.draw()
    blit_noCollide_tile(tmxdata)

    for coin in coins:
        coin.draw()

    for chest in chests:
        chest.draw()

    for goal in goals:
        goal.draw()

    for enemy in enemies[current_level-1]:
        if enemy.name == 'Skull':
            for projectile in enemy.attackHitbox:
                if enemy.left:
                    screen.blit(pygame.transform.flip(enemy.projectileImage, True, False), projectile[0])
                else:
                    screen.blit(enemy.projectileImage, projectile[0])
        enemy.draw()

    player.draw()

    for enemy in enemies[current_level-1]:
        enemy.drawHealth()

    player.drawHealth()

    for flame in flames:
        flame.draw()

    for arrow in arrows:
        arrow.draw()

    for text in texts:
        text.draw()

    #(DEBUGGING)
    # player coordinates
    # cordHitbox = displayFont.render(str(player.hitbox), False, (0, 255, 0))
    # screen.blit(cordHitbox, (0, 16))

    # fps counter
    # fpsText = displayFont.render(str('FPS: '+str(int(clock.get_fps()))), False, (0, 255, 0))
    # screen.blit(fpsText, (0, 0))

goals = parse(tmxdata)
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if player.attacking == False and player.healing == False:
                if player.inventory[player.equippedSlot-1] != 'unequipped':
                    player.equippedItem = player.inventory[player.equippedSlot-1]
                    if player.inventory[player.equippedSlot-1] == 'health potion':
                        player.healing = True
                        healSound.play()
                    else:
                        player.attacking = True

                        equippedItemData = player.equippedItem.split(' ')
                        player.attackMaxTime = weaponsData[equippedItemData[0]][equippedItemData[1]]['speed']*1000
                        if equippedItemData[1] == 'axe':
                            axeSounds[0].play()
                        elif equippedItemData[1] == 'sword':
                            swordSounds[0].play()
                        elif equippedItemData[1] == 'dagger':
                            daggerSounds[0].play()

    if player.equippedItem != 'unequipped':
        if player.healing:
            healingInterval = player.healthDelay / (player.healthMaxDelay // player.healthHealed)
            if player.healthDelay >= player.healthMaxDelay:
                player.healing = False
                player.healthDelay = 0
                player.inventory[player.equippedSlot-1] = 'unequipped'
            elif math.floor(healingInterval) == int(healingInterval):
                player.heal()
            player.healthDelay += 1000/FPS
        elif player.attacking:
            if player.attackTime >= player.attackMaxTime:
                player.attacking = False
                player.attackTime = 0
                player.attackHitbox.clear()
                for enemy in enemies[current_level-1]:
                    enemy.isAttacked = False
            player.attackTime += 1000/FPS

    if last_level != current_level:
        player.hitbox.left, player.hitbox.top = spawns[last_level][0], spawns[last_level][1]
        goals = parse(tmxdata)
        fade(width * unit, (height-2) * unit, 300, 0, -1)
    last_level = current_level

    # check if player attack hitboxes hit enemy(deal damage).
    delete = []
    if len(enemies[current_level-1]) != 0:
        for enemy in enemies[current_level-1]:
            for weapon in player.attackHitbox:
                if player.attackHitbox[weapon].colliderect(enemy.hitbox):
                    playerequippedItemData = player.equippedItem.split(' ')
                    if enemy.isAttacked == False and enemy.attacking == False:
                        if playerequippedItemData[1] == 'axe':
                            axeSounds[1].play()
                        elif playerequippedItemData[1] == 'sword':
                            swordSounds[1].play()
                        elif playerequippedItemData[1] == 'dagger':
                            daggerSounds[1].play()
                        if enemy.health - weaponsData[equippedItemData[0]][equippedItemData[1]]['damage'] <= 0:
                            delete.append(enemies[current_level-1].index(enemy))
                            player.enemyKilled += 1
                        else:
                            enemy.health -= weaponsData[equippedItemData[0]][equippedItemData[1]]['damage']
                        texts.append(textDisplay(player.attackHitbox[weapon].x, player.attackHitbox[weapon].y, '-'+str(int(weaponsData[equippedItemData[0]][equippedItemData[1]]['damage'])), (50, 255, 50)))
                        enemy.isAttacked = True
    for index in delete:
        enemies[current_level-1].pop(index)
    # check if player hitbox collides which enemy(take damage).
    for enemy in enemies[current_level-1]:
        for weapon in enemy.attackHitbox:
            if enemy.name == 'Skull':
                if player.hitbox.colliderect(weapon[0]):
                    if player.isAttacked == False:
                        if player.health - enemy.damage <= 0:
                            displayMessage(width * unit, height * unit, 'You died.', (255, 50, 50))
                        else:
                            enemy.attackHitbox.remove(weapon)
                            player.health -= enemy.damage
                        texts.append(textDisplay(player.hitbox.x, player.hitbox.y, '-'+str(int(enemy.damage)), (255, 50, 50)))
                        player.isAttacked = True
            else:
                if player.hitbox.colliderect(enemy.attackHitbox[weapon]):
                    if player.isAttacked == False:
                        if player.health - enemy.damage <= 0:
                            displayMessage(width * unit, height * unit, 'You died.', (255, 50, 50))
                        else:
                            player.health -= enemy.damage
                        texts.append(textDisplay(player.hitbox.x, player.hitbox.y, '-'+str(int(enemy.damage)), (255, 50, 50)))
                        player.isAttacked = True
        else:#first attack hitboxes, then check body collision(only one will happen)
            if player.hitbox.colliderect(enemy.hitbox):
                if player.isAttacked == False:
                    if player.health - 1 <= 0:
                        displayMessage(width * unit, height * unit, 'You died.', (255, 50, 50))
                    else:
                        player.health -= 1
                    texts.append(textDisplay(player.hitbox.x, player.hitbox.y, '-'+str(1), (255, 50, 50)))
                    player.isAttacked = True
    if player.isAttacked:
        if player.attackedDelay >= player.attackedMaxDelay:
            player.isAttacked = False
            player.attackedDelay = 0
            player.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/priests_idle/priest2/v1/priest2_v1_"+str(i+1)+".png"), (unit, unit)) for i in range(4)]
        else:
            player.attackedDelay += 1000/FPS
            player.sprite = [pygame.transform.scale(pygame.image.load("assets/2D Pixel Dungeon Asset Pack/Character_animation/priests_idle/priest2/v2/priest2_v2_"+str(i+1)+".png"), (unit, unit)) for i in range(4)]

    # Move the player if an arrow key is pressed
    key = pygame.key.get_pressed()
    if key[pygame.K_a]:
        player.vel[0] += -player.speed
        player.left = True
        player.right = False
    if key[pygame.K_d]:
        player.vel[0] += player.speed
        player.left = False
        player.right = True
    if key[pygame.K_w]:
        player.vel[1] += -player.speed
    if key[pygame.K_s]:
        player.vel[1] += player.speed
    # if key[pygame.K_SPACE]: (DEBUG)
    #     increase = 2
    #     if not player.health + increase >= player.healthMax:
    #         player.health += 2
    player.move()
    player.vel = [0, 0]

    if len(enemies[current_level-1]) != 0:
        for enemy in enemies[current_level-1]:
            enemy.move()

    for enemy in enemies[current_level-1]:
        if enemy.name == 'Skull':
            for projectile in enemy.attackHitbox:
                enemy.moveProjectile(enemy.attackHitbox.index(projectile))

    # Check for number key presses to equip inventory.
    if player.attacking == False and player.healing == False:
        if key[pygame.K_1]:
            player.equippedSlot = 1
        elif key[pygame.K_2]:
            player.equippedSlot = 2
        elif key[pygame.K_3]:
            player.equippedSlot = 3
        elif key[pygame.K_4]:
            player.equippedSlot = 4
        elif key[pygame.K_5]:
            player.equippedSlot = 5
        elif key[pygame.K_6]:
            player.equippedSlot = 6

    # Draw the scene
    redrawGameWindow()

    if len(enemies[current_level-1]) == 0:
        goalPass = True
    else:
        goalPass = False

    if goalPass != goalLastPass:
        goals = parse(tmxdata)
    goalLastPass = goalPass

    # Check if enemies are defeated and next to goal then switch maps.
    if goalPass and player.hitbox.colliderect(goalZone[current_level-1]):
        key = pygame.key.get_pressed()
        if len(arrows) == 0:
            arrows.append(Arrow(arrowPos[current_level-1][0], arrowPos[current_level-1][1]))
        if key[pygame.K_e]:
            fadeSound.play()
            if current_level + 1 > max_level:
                score = player.coins + player.keys + player.enemyKilled
                for item in player.inventory:
                    if item != 'unequipped':
                        if item == 'health potion':
                            score += 2
                        else:
                            itemData = item.split(' ')
                            score += weaponsData[itemData[0]][itemData[1]]['value']
                displayMessage(width * unit, height * unit, ["You completed the game!", "Score: "+str(score)], (255, 235, 50))
            fade(width * unit, (height-2) * unit, 0, 300, 1)
            current_level += 1
            arrows.clear()
            print("You past level", str(last_level)+"!")
            tmxdata = load_pygame("maps\level"+str(current_level)+".tmx")
    else:
        arrows.clear()

    pygame.display.flip()
pygame.quit()
sys.exit()