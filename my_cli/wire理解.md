

 在soul 的init中 , 存在各种方法供外部使用 ,

(**wire类  作为一个 定义的 队列类 , 其中包含了"Soul 层发送消息" 和 "Soul 层接收消息" 的方法 , 通过队列的方式 , 将消息发送到对应的队列中**)

 create_soul 作为其中的一个方法 , 将配置 :Agent,Runtime等 作为参数传递给了 kimisoul
 (kimisoul实现Soul(Protocol) 这个类似接口 的协议类中的方法 , 其中run方法 会将 将AI的回复 加入消息队列中 )


 run_soul : 
        
        1. 会创建 Wire 
        
        2. 会启动 UI Loop 任务
        
        3. 启动 Soul 任务 (也就是将AI的回复 加入消息队列中等 : 同时异步处理"哪个先完成就处理哪个")
                        ( 与此同时 , 也会将 AI消息 加入 "context" 这个上下文窗口中 )
        4. 收尾 (例如"关闭 Wire " , "关闭 UI Loop " , "关闭 Soul 任务" 等)


(ContextVar  是一个上下文变量 , 用来存储当前线程的上下文信息 : 从而实现 上下文隔离 , 不会在并发任务间互相干扰)

( UI Loop 任务 : 用来处理UI的显示 , 也就是将消息队列中的消息 , 显示到UI上)

