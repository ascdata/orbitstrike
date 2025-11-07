import pyxel
import random

WIDTH = 480
HEIGHT = 360

class SpaceShooter:
    def __init__(self):
        # Spieler
        self.ship_x = WIDTH // 2
        self.ship_y = HEIGHT // 2
        self.ship_size = 16
        self.hp = 10

        # Bullets
        self.bullets = []
        self.enemy_bullets = []
        self.rockets = []  # Raketen bei Rechtsklick

        # Planeten
        self.planets = []

        # Explosionen
        self.explosions = []

        # Sterne
        self.stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1,2)] for _ in range(100)]

        # Score
        self.score = 0

        # Hitze
        self.heat = 0
        self.max_heat = 30
        self.overheated = False

        # Boss
        self.boss = None  # [type,x,y,hp,max_hp]
        self.boss_defeated = set()

        pyxel.run(self.update, self.draw)

    def spawn_planet(self):
        x = pyxel.rndi(0, WIDTH-16)
        y = 0
        color = random.choice([9,10,11,12,13,14])
        self.planets.append([x, y, color])

    def spawn_boss(self, boss_type):
        if boss_type in self.boss_defeated:
            return
        if boss_type == "galaxy":
            self.boss = ["galaxy", WIDTH//2-32, 0, 50, 50]
        elif boss_type == "pirate":
            self.boss = ["pirate", WIDTH//2-32, 0, 10, 10]

    def update(self):
        # Maussteuerung
        target_x = max(0, min(WIDTH-self.ship_size, pyxel.mouse_x))
        target_y = max(0, min(HEIGHT-self.ship_size, pyxel.mouse_y))
        self.ship_x += (target_x - self.ship_x)*0.1
        self.ship_y += (target_y - self.ship_y)*0.1

        # Schießen mit links
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and not self.overheated:
            self.bullets.append([self.ship_x+self.ship_size//2, self.ship_y])
            self.heat += 1
            if self.heat >= self.max_heat:
                self.overheated = True
        if self.heat>0:
            self.heat -= 0.3
        if self.overheated and self.heat<=0:
            self.heat=0
            self.overheated=False

        # Rakete mit rechts
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            self.rockets.append([self.ship_x+self.ship_size//2, self.ship_y, 0, 4])  # x,y,timer,dmg

        # Bullets bewegen
        self.bullets = [[bx, by-6] for bx, by in self.bullets if by-6>=0]

        # Planeten bewegen
        if pyxel.frame_count % 50 == 0 and self.boss is None:
            self.spawn_planet()
        new_planets = []
        for px, py, color in self.planets:
            py += 1
            dx = self.ship_x + self.ship_size/2 - (px + 8)
            dy = self.ship_y + self.ship_size/2 - (py + 8)
            if dx*dx + dy*dy <= (self.ship_size/2 + 8)**2:
                self.hp -= 2.5
                self.explosions.append([self.ship_x, self.ship_y, 16])
            hit = False
            for bullet in self.bullets:
                if (bullet[0]-px-8)**2 + (bullet[1]-py-8)**2 <= 64:
                    hit = True
                    self.score += 1
                    self.bullets.remove(bullet)
                    self.explosions.append([px+8, py+8, 16])
                    break
            if not hit and py<HEIGHT:
                new_planets.append([px, py, color])
        self.planets = new_planets

        # Boss spawnen
        if self.boss is None:
            if self.score >= 5 and "galaxy" not in self.boss_defeated:
                self.spawn_boss("galaxy")
            elif self.score >= 10 and "pirate" not in self.boss_defeated:
                self.spawn_boss("pirate")

        # Boss update
        if self.boss:
            btype, bx, by, hp, max_hp = self.boss
            if btype=="pirate":
                # von links nach rechts
                direction = getattr(self, "pirate_dir", 1)
                bx += 1*direction
                if bx <= 0 or bx >= WIDTH-64:
                    self.pirate_dir = -direction
                else:
                    self.pirate_dir = direction
            by += 0.3
            dx = self.ship_x + self.ship_size/2 - (bx + 32)
            dy = self.ship_y + self.ship_size/2 - (by + 32)
            if dx*dx + dy*dy <= (self.ship_size/2 + 32)**2:
                self.hp -= 2.5
                self.explosions.append([self.ship_x, self.ship_y, 16])
            bullets_to_remove=[]
            for bullet in self.bullets:
                dx = bx+32 - bullet[0]
                dy = by+32 - bullet[1]
                if dx*dx+dy*dy <= 32*32:
                    hp -= 1
                    bullets_to_remove.append(bullet)
                    self.explosions.append([bx+32, by+32,16])
            for b in bullets_to_remove:
                if b in self.bullets:
                    self.bullets.remove(b)
            # Pirate feuert zurück
            if btype=="pirate" and pyxel.frame_count%30==0:
                self.enemy_bullets.append([bx+32, by+32])
            if hp<=0:
                self.boss_defeated.add(btype)
                self.boss=None
            else:
                self.boss=[btype,bx,by,hp,max_hp]

        # Enemy bullets bewegen
        new_enemy_bullets=[]
        for bx,by in self.enemy_bullets:
            by+=4
            if (bx-(self.ship_x+self.ship_size/2))**2 + (by-(self.ship_y+self.ship_size/2))**2 <= (self.ship_size/2)**2:
                self.hp-=1
                self.explosions.append([self.ship_x,self.ship_y,16])
            else:
                if by<=HEIGHT:
                    new_enemy_bullets.append([bx,by])
        self.enemy_bullets=new_enemy_bullets

        # Raketen bewegen
        new_rockets=[]
        for rx, ry, prog, dmg in self.rockets:
            ry -= 6
            prog +=1
            exploded = False
            if self.boss:
                btype, bx, by, hp, max_hp = self.boss
                if bx <= rx <= bx+64 and by <= ry <= by+64:
                    hp -= 4  # 4x dmg
                    exploded=True
                    self.explosions.append([rx,ry,16])
                    if hp<=0:
                        self.boss_defeated.add(btype)
                        self.boss=None
                    else:
                        self.boss=[btype,bx,by,hp,max_hp]
            if not exploded and ry>=0:
                new_rockets.append([rx,ry,prog,dmg])
        self.rockets = new_rockets

        # Explosionen
        self.explosions=[[ex,ey,timer-1] for ex,ey,timer in self.explosions if timer-1>0]

        # Sterne
        for star in self.stars:
            star[1] += star[2]
            if star[1]>HEIGHT:
                star[0]=random.randint(0,WIDTH)
                star[1]=0

    def draw_spaceship(self,x,y,color,down=False):
        # down=True für Piratenschiff nach unten
        if down:
            # Spitze nach unten
            pyxel.tri(x+8,y+16,x+4,y,x+12,y,color)
            # Flügel
            pyxel.tri(x,y,x+4,y,x+4,y-4,color)
            pyxel.tri(x+12,y,x+16,y,x+12,y-4,color)
            # Cockpit
            pyxel.rect(x+6,y+6,4,4,11)
            # Triebwerke oben
            pyxel.tri(x+4,y-4,x+8,y,x+8,y-4,9)
            pyxel.tri(x+8,y-4,x+12,y,x+12,y-4,9)
        else:
            pyxel.tri(x+8, y, x+4, y+12, x+12, y+12, color)
            pyxel.tri(x, y+12, x+4, y+12, x+4, y+16, color)
            pyxel.tri(x+12, y+12, x+16, y+12, x+12, y+16, color)
            pyxel.rect(x+6,y+6,4,4,11)
            pyxel.tri(x+4,y+16,x+8,y+12,x+8,y+16,9)
            pyxel.tri(x+8,y+16,x+12,y+12,x+12,y+16,9)

    def draw(self):
        pyxel.cls(0)
        # Sterne
        for x,y,size in self.stars:
            pyxel.pset(x,y,7)

        # Spieler
        self.draw_spaceship(self.ship_x,self.ship_y,10)

        # Bullets
        for bx,by in self.bullets:
            pyxel.rect(bx,by,4,8,11)

        # Planeten
        for px,py,color in self.planets:
            pyxel.circ(px+8,py+8,8,color)

        # Boss
        if self.boss:
            btype,bx,by,hp,max_hp=self.boss
            if btype=="galaxy":
                pyxel.circ(bx+32,by+32,32,14)
                pyxel.circb(bx+32,by+32,36,7)
                pyxel.circb(bx+32,by+32,40,7)
            else:
                self.draw_spaceship(bx,by,8,down=True)

        # Enemy bullets
        for bx,by in self.enemy_bullets:
            pyxel.rect(bx,by,4,4,8)

        # Raketen
        for rx,ry,prog,dmg in self.rockets:
            pyxel.rect(rx-1,ry-4,2,8,12)

        # Explosionen
        for ex,ey,timer in self.explosions:
            pyxel.circ(ex,ey,timer,10)

        # HP
        pyxel.rect(10, HEIGHT-50, 100,10,7)
        pyxel.rect(10, HEIGHT-50, int(100*(self.hp/10)),10,8)
        pyxel.text(10, HEIGHT-65, f"Score: {self.score}",11)

        # Hitze
        heat_width = int((self.heat/self.max_heat)*100)
        pyxel.rect(10, HEIGHT-35,100,10,7)
        pyxel.rect(10, HEIGHT-35,heat_width,10,10)

        # Boss HP
        if self.boss:
            _,_,_,hp,max_hp=self.boss
            pyxel.rect(WIDTH-120,20,100,10,7)
            pyxel.rect(WIDTH-120,20,int(100*(hp/max_hp)),10,11)

        # Game Over
        if self.hp<=0:
            pyxel.text(WIDTH//2-60, HEIGHT//2, "GAME OVER",8)

pyxel.init(WIDTH, HEIGHT, title="Space Shooter Multi-Boss")
SpaceShooter()
