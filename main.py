from __future__ import division
from collections import namedtuple
import json
import math
from random import randint, random

from kivy import platform                           #kivy modülü import edildi ve alt kütüphaneleri kullanıldı.
from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.config import Config

Config.set('graphics', 'width', '960')              #oyun programının çalışacağı ekranın boyutu ayarlandı.
Config.set('graphics', 'height', '540')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'show_cursor', '0')
Config.set('input', 'mouse', 'mouse,disable_multitouch')            #mouse ile multitouch özelliği disable edildi.

from kivy.core.audio import SoundLoader
from kivy.core.image import Image                   #kivy modülünün alt kütüphaneleri import edildi. 
from kivy.core.window import Window
from kivy.graphics import Mesh
from kivy.graphics.instructions import RenderContext
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

UVMapping = namedtuple('UVMapping', 'u0 v0 u1 v1 su sv')


def load_atlas(atlas_name):                             #arka planın eklenmesi sağlandı.
    with open(atlas_name, 'rb') as f:
        atlas = json.loads(f.read().decode('utf-8'))

    tex_name, mapping = atlas.popitem()
    tex = Image(tex_name).texture
    tex_width, tex_height = tex.size

    uvmap = {}
    for name, val in mapping.items():
        x0, y0, w, h = val
        x1, y1 = x0 + w, y0 + h
        uvmap[name] = UVMapping(
            x0 / tex_width, 1 - y1 / tex_height,
            x1 / tex_width, 1 - y0 / tex_height,
            0.5 * w, 0.5 * h)

    return tex, uvmap


class Particle:                                     #particle sınıfı oluşturuldu.
    x = 0
    y = 0
    size = 1

    def __init__(self, parent, i):                  
        self.parent = parent                         #parent fonksiyonlarının kullanılması amaçlandı.
        self.vsize = parent.vsize                    #yatay boyut ayarlaması yapıldı.
        self.base_i = 4 * i * self.vsize             
        self.reset(created=True)                     #oluşturma olayı true olarak setlendi.

    def update(self):                                #update fonksiyonu oluşturuldu.
        for i in range(self.base_i,                  #yatay boyut ayarlandı ve ilk değer ataması ayarlandı.
                       self.base_i + 4 * self.vsize,
                       self.vsize):
            self.parent.vertices[i:i + 3] = (
                self.x, self.y, self.size)

    def reset(self, created=False):                   #reset fonksiyonu ayarlandı. 
        raise NotImplementedError()                   #Soyut yöntemler yöntemi geçersiz kılsın

    def advance(self, nap):                           #advance fonksiyonu ayarlandı.
        raise NotImplementedError()                   #Soyut yöntemler yöntemi geçersiz kılsın


class PSWidget(Widget):                               #widget sınıfı oluşturuldu.
    indices = []                                      #indis listesi
    vertices = []                                     #köşe listesi
    particles = []                                    #particles listesi

    def __init__(self, **kwargs):                                       #Pencere ayarlaması yapıldı.
        Widget.__init__(self, **kwargs)
        self.canvas = RenderContext(use_parent_projection=True)
        self.canvas.shader.source = self.glsl

        self.vfmt = (
            (b'vCenter', 2, 'float'),
            (b'vScale', 1, 'float'),
            (b'vPosition', 2, 'float'),
            (b'vTexCoords0', 2, 'float'),
        )

        self.vsize = sum(attr[1] for attr in self.vfmt)

        self.texture, self.uvmap = load_atlas(self.atlas)

    def make_particles(self, Cls, num):                                     #Particle oluşturma fonksiyonu tanımlandı.
        count = len(self.particles)
        uv = self.uvmap[Cls.tex_name]

        for i in range(count, count + num):
            j = 4 * i
            self.indices.extend((
                j, j + 1, j + 2, j + 2, j + 3, j))

            self.vertices.extend((                                           #particle konumlanması amaçlandı.
                0, 0, 1, -uv.su, -uv.sv, uv.u0, uv.v1,
                0, 0, 1,  uv.su, -uv.sv, uv.u1, uv.v1,
                0, 0, 1,  uv.su,  uv.sv, uv.u1, uv.v0,
                0, 0, 1, -uv.su,  uv.sv, uv.u0, uv.v0,
            ))

            p = Cls(self, i)
            self.particles.append(p)

    def update_glsl(self, nap):                                                 #update fonksiyonu oluşturuldu.
        for p in self.particles:
            p.advance(nap)                                                      #advance fonksiyonu çağırıldı.
            p.update()                                                          #update fonksiyonu çağırıldı.

        self.canvas.clear()                                                     #pencerenin temizlenmesi sağlandı.

        with self.canvas:
            Mesh(fmt=self.vfmt, mode='triangles',                               
                 indices=self.indices, vertices=self.vertices,
                 texture=self.texture)



class Star(Particle):                                                           #star sınıfı oluşturuldu.
    plane = 1                                                                   #uçak değeri 1 olarak setlendi
    tex_name = 'star'                                                           #arka plandaki yıldızların oluşumu amaçlandı. Uzay efekti verebilmek amacıyla.

    def reset(self, created=False):                                             #reset fonksiyonu oluşturuldu.
        self.plane = randint(1, 3)                                              #plane değişkeni 1-3 arası random değer üretilerek setlendi.
                                                                                #aynı anda gelebilecek düşman sayısı
        if created:
            self.x = random() * self.parent.width                               #boyut ayarlaması yapıldı.
        else:
            self.x = self.parent.width                                          #boyut ayarlaması yapıldı.

        self.y = random() * self.parent.height                                  #boyut ayarlaması yapıldı.
        self.size = 0.1 * self.plane                                            #boyut ayarlaması yapıldı.

    def advance(self, nap):                                                     #advance fonksiyonu oluşturuldu. 
        self.x -= 20 * self.plane * nap                                         
        if self.x < 0:
            self.reset()


class Player(Particle):                                                       #player sınıfı oluşturuldu.
    tex_name = 'player'

    def reset(self, created=False):                                            #oyunun resetlenmesi durumunda çalışacak olan fonksiyon
        self.x = self.parent.player_x
        self.y = self.parent.player_y

    advance = reset


class Trail(Particle):                                                      #trail fonksiyonu oluşturuldu.
    tex_name = 'trail'

    def reset(self, created=False):
        self.x = self.parent.player_x + randint(-30, -20)                   #oyuncunun kontrolündeki nesnenin arkasından iz bırakması sağlandı.
        self.y = self.parent.player_y + randint(-10, 10)

        if created:                                                         #eğer yeni oluşturulmuş ise boyutu 0 olarak ayarlandı.
            self.size = 0
        else:
            self.size = random() + 0.6                                      #uçağın hareketinden sonra iz boyutu random olarak ayarlandı.

    def advance(self, nap):
        self.size -= nap
        if self.size <= 0.1:
            self.reset()
        else:
            self.x -= 120 * nap


class Bullet(Particle):                                                     #mermi sınıfı oluşturuldu.
    active = False
    tex_name = 'bullet'

    def reset(self, created=False):                                         #aktif edilirse gideceği yön ayarlaması yapıldı.
        self.active = False
        self.x = -100
        self.y = -100

    def advance(self, nap):
        if self.active:
            self.x += 250 * nap
            if self.x > self.parent.width:
                self.reset()

        elif (self.parent.firing and                                        #ateş butonuna basılı tutulması durumundaki opsiyon ayarlandı.
              self.parent.fire_delay <= 0):
            snd_laser.play()

            self.active = True
            self.x = self.parent.player_x + 40
            self.y = self.parent.player_y
            self.parent.fire_delay += 0.3333                                #ateşin gecikmesi ayarlandı.


class Enemy(Particle):                                                      #düşman sınıfı oluşturuldu.
    active = False
    tex_name = 'ufo'
    v = 0

    def reset(self, created=False):                                         #düşmanların yeniden gelmesi için reset fonksiyonu ayarlandı.
        self.active = False
        self.x = -100
        self.y = -100
        self.v = 0

    def advance(self, nap):
        if self.active:
            if self.check_hit():                                             #ateş ile çarpma durumu kontrol edildi.
                snd_hit.play()                                               #çarpma söz konusu ise reset fonksiyonu aktif edildi.

                self.reset()
                return

            self.x -= 200 * nap                                              #yeni gelecek düşmanın boyut ayarlaması yapıldı.
            if self.x < -50:
                self.reset()
                return

            self.y += self.v * nap                                          #yeni gelecek düşmanın boyut ayarlaması yapıldı.
            if self.y <= 0:
                self.v = abs(self.v)
            elif self.y >= self.parent.height:
                self.v = -abs(self.v)

        elif self.parent.spawn_delay <= 0:                                  #düşman aktif edildi ve tekrar gönderilmesi amaçlandı.
            self.active = True
            self.x = self.parent.width + 50
            self.y = self.parent.height * random()
            self.v = randint(-100, 100)
            self.parent.spawn_delay += 1

    def check_hit(self):                                                    #düşman ile merminin çarpışıp çarpışmadığını kontrol eden fonksiyon
        if math.hypot(self.parent.player_x - self.x,
                      self.parent.player_y - self.y) < 60:
            return True

        for b in self.parent.bullets:
            if not b.active:
                continue

            if math.hypot(b.x - self.x, b.y - self.y) < 30:
                b.reset()
                return True


class Game(PSWidget):                                                       #oyun sınıfı oluşturuldu.
    glsl = 'game.glsl'
    atlas = 'game.atlas'

    firing = False
    fire_delay = 0
    spawn_delay = 1                                                         #tekrar resetleme aktif edildi.

    use_mouse = platform not in ('ios', 'android')                          #platform android veya ios değilse mouse kullanılması ayarlandı.

    def initialize(self):                                                   #ilk açılma aşaması ayarlandı.  
        self.player_x, self.player_y = self.center                          #ekran ortalandı.

        self.make_particles(Star, 200)                                      #ilk açılıştaki arka plan ayarlamaları için setlemeler yapıldı.
        self.make_particles(Trail, 200) 
        self.make_particles(Player, 1)
        self.make_particles(Enemy, 25)
        self.make_particles(Bullet, 25)

        self.bullets = self.particles[-25:]

    def update_glsl(self, nap):                                             #mouse kullanıldığında çalışacak opsiyonlar ayarlandı.
        if self.use_mouse:
            self.player_x, self.player_y = Window.mouse_pos

        if self.firing:                                                     #sürekli ateş durumunda gecikme görselliği ayarlandı.
            self.fire_delay -= nap

        self.spawn_delay -= nap

        PSWidget.update_glsl(self, nap)

    def on_touch_down(self, touch):                                         #android veya ios cihazlar için touch_down fonksiyonu oluşturuldu.
        self.player_x, self.player_y = touch.pos
        self.firing = True
        self.fire_delay = 0

    def on_touch_move(self, touch):                                         #android veya ios cihazlar için touch_move fonksiyonu oluşturuldu.
        self.player_x, self.player_y = touch.pos

    def on_touch_up(self, touch):                                           #android veya ios cihazlar için touch_up fonksiyonu oluşturuldu.
        self.firing = False


class GameApp(App):                                                         
    def build(self):
        EventLoop.ensure_window()
        return Game()

    def on_start(self):                                                     #başlangıçta saat ayarlaması başlatıldı.
        self.root.initialize()                                             
        Clock.schedule_interval(self.root.update_glsl, 60 ** -1)

if __name__ == '__main__':
    Window.clearcolor = get_color_from_hex('111110')

    GameApp().run()
