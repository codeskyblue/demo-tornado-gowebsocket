package main

import (
	"context"
	"encoding/json"
	"log"
	"time"

	"github.com/gorilla/websocket"
)

// var upgrader = websocket.Upgrader{
// 	ReadBufferSize:  1024,
// 	WriteBufferSize: 1024,
// }

func wsDialContext(ctx context.Context, urlStr string) (*websocket.Conn, error) {
	ctx, cancel := context.WithCancel(ctx)
	c, _, err := websocket.DefaultDialer.DialContext(ctx, urlStr, nil)
	if err != nil {
		return nil, err
	}
	const pingTimeout = 1 * time.Second
	go func() {
		pongC := make(chan bool)
		c.SetPongHandler(func(data string) error {
			log.Println("receive pong", data)
			pongC <- true
			return nil
		})

		t := time.NewTicker(3 * time.Second)
		defer t.Stop()
		for {
			// send PING
			select {
			case <-t.C:
				c.WriteMessage(websocket.PingMessage, []byte("gorilla"))
			case <-ctx.Done():
				return
			}
			// wait PONG
			select {
			case <-pongC:
			case <-time.After(pingTimeout):
				cancel()
				return
			case <-ctx.Done():
				return
			}
		}
	}()
	return c, nil
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	c, err := wsDialContext(ctx, "ws://localhost:7000/ws/echo")
	if err != nil {
		log.Fatal(err)
	}
	defer c.Close()

	go func() {
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				log.Println("read:", err)
				return
			}
			log.Printf("recv: %s", message)
		}
	}()

	v := map[string]string{
		"id": "12345",
	}
	data, _ := json.Marshal(v)
	c.WriteMessage(websocket.TextMessage, data)
	time.Sleep(5 * time.Second)
	cancel()
	select {
	case <-ctx.Done():
		print("ERROR Quit")
	}
	time.Sleep(1 * time.Second)
}
