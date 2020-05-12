 //-----------------------------------------------------
 // Design Name : Input Buffer
 // Function    : Circular queue of vectors for up to IB_DEPTH cycles
 //-----------------------------------------------------
`include "ram_dual_port.sv"

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

    parameter LATENCY = 2;
    parameter RAM_LATENCY = LATENCY-1;
    parameter MEM_WIDTH = N*DATA_WIDTH;

    //-------------Code Start-----------------

    // Instantiate memory to implement queue
    reg [$clog2(IB_DEPTH)-1:0] mem_address_a=2;
    reg [$clog2(IB_DEPTH)-1:0] mem_address_b=0;
    reg mem_write_enable_a=1;
    reg mem_write_enable_b=0;
    reg [MEM_WIDTH-1:0] mem_in_a=0;
    reg [MEM_WIDTH-1:0] mem_in_b=0;
    wire [MEM_WIDTH-1:0] mem_out_a=0;
    wire [MEM_WIDTH-1:0] mem_out_b=0;
    ram_dual_port mem (
      .clk( clk ),
      .clken( !memory_controller_waitrequest ),
      .address_a( mem_address_a ),
      .address_b( mem_address_b ),
      .wren_a( mem_write_enable_a ),
      .wren_b( mem_write_enable_b ),
      .data_a( mem_in_a ),
      .data_b( mem_in_b ),
      .byteena_a( 1'b1 ),
      .byteena_b( 1'b1 ),
      .q_a( mem_out_a ),
      .q_b( mem_out_b)
    );
    defparam mem.width_a = MEM_WIDTH;
    defparam mem.width_b = MEM_WIDTH;
    defparam mem.widthad_a = $clog2(IB_DEPTH);
    defparam mem.widthad_b = $clog2(IB_DEPTH);
    defparam mem.width_be_a = 1;
    defparam mem.width_be_b = 1;
    defparam mem.numwords_a = IB_DEPTH;
    defparam mem.numwords_b = IB_DEPTH;
    defparam mem.latency = RAM_LATENCY;
    defparam mem.init_file = "inputBuffer.mif";

    always @(posedge clk) begin

        // Logic for enqueuing values
        mem_in_a <= { << { vector_in }};
        mem_address_a <= enqueue ? mem_address_a+1'b1 : mem_address_a;
        mem_write_enable_a <= enqueue;

        //Logic for dequeuing
        mem_address_b <= dequeue ? mem_address_b+1'b1 : mem_address_b;

    end

    /*
    // OLD ONE FOR REFERENCE
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
    end*/

    assign eof_out = eof_in;
    assign vector_out = { >> { mem_out_b }};

 
 endmodule 