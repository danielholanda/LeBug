 //-----------------------------------------------------
 // Design Name : Input Buffer
 // Function    : Circular queue of vectors for up to IB_DEPTH cycles
 //-----------------------------------------------------
 module  inputBuffer #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  parameter IB_DEPTH=4
  )
  (
  input logic clk,
  input logic enqueue,
  input logic eof_in,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg valid_out,
  output reg eof_out,
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0]
 );
    //----------Internal Variables------------
    reg [(DATA_WIDTH*N)-1:0] mem_array [IB_DEPTH-1 : 0];
    reg mem_array_valid [IB_DEPTH-1 : 0];
    reg [7:0] head = 8'b0;
    reg [7:0] tail = 8'b0;
    reg dequeue=1'b1; // THIS SHOULD BECOME AN INPUT LATER

    //-------------Code Start-----------------


    always @(posedge clk) begin
      // Store valid inputs in buffer 
        if (enqueue==1'b1) begin
            mem_array[head]<= { << { vector_in }};
            mem_array_valid[head] <= enqueue;
            head <= head+1;
        end

        // Output values when "dequeue" is high
        if (dequeue==1'b1) begin
            valid_out <= { >> { mem_array_valid[tail] }};
            tail <= tail+1;
        end
    end

    assign eof_out = eof_in;
    assign vector_out = vector_in;
 
 endmodule 