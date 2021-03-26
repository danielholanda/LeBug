 //-----------------------------------------------------
 // Design Name : Vector Vector ALU
 // Function    : Performs simple vector ops
 //-----------------------------------------------------

 module  vectorVectorALU #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  parameter MAX_CHAINS=4,
  parameter PERSONAL_CONFIG_ID=0,
  parameter VVVRF_SIZE=8,
  parameter DATA_TYPE=0,
  parameter [7:0] INITIAL_FIRMWARE_OP         [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_ADDR_RD    [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_COND       [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_CACHE      [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_CACHE_ADDR [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_MINICACHE  [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_CACHE_COND [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}}
  )
  (
  input logic clk,
  input logic tracing,
  input logic valid_in,
  input logic [1:0] eof_in,
  input logic [1:0] bof_in,
  input logic [$clog2(MAX_CHAINS)-1:0] chainId_in,
  input logic [7:0] configId,
  input logic [7:0] configData,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0],
  output reg [$clog2(MAX_CHAINS)-1:0] chainId_out,
  output reg valid_out,
  output reg [1:0] eof_out,
  output reg [1:0] bof_out
 );

    //----------Internal Variables------------
    reg [7:0] firmware_op         [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_OP;
    reg [7:0] firmware_addr_rd    [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_ADDR_RD;
    reg [7:0] firmware_cond       [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_COND;
    reg [7:0] firmware_cache      [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_CACHE;
    reg [7:0] firmware_cache_addr [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_CACHE_ADDR;
    reg [7:0] firmware_minicache  [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_MINICACHE;
    reg [7:0] firmware_cahce_cond [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_CACHE_COND;
    reg [DATA_WIDTH-1:0] valid_result [N-1:0];
    reg [DATA_WIDTH-1:0] mini_cache [N-1:0];
    reg [7:0] firmware_minicache_delay;
    reg [7:0] firmware_minicache_delay_2;
    reg [DATA_WIDTH-1:0] vector_in_delay [N-1:0];
    reg [DATA_WIDTH*2-1:0] operator_se [N-1:0];
    reg [$clog2(MAX_CHAINS)-1:0] chainId_in_delay=0;
    reg valid_in_delay = 1'b0;
    reg valid_in_delay_2 = 1'b0;
    reg [1:0] eof_in_delay = 2'b00;
    reg [1:0] bof_in_delay = 2'b00;
    reg [7:0] firmware_op_delay = 0;
    reg [7:0] firmware_cache_delay = 0;
    reg [7:0] firmware_cache_delay_2 = 0;
    reg [7:0] firmware_cache_addr_delay = 0;
    reg [7:0] firmware_cache_addr_delay_2 = 0;
    reg [7:0] firmware_cond_delay =0;
    reg [7:0] firmware_cache_cond =0;
    reg [7:0] firmware_cache_cond_delay =0;
    reg cond_valid, cache_cond_valid;
    reg [DATA_WIDTH-1:0] operator [N-1:0];
    reg [DATA_WIDTH-1:0] operand [N-1:0];
    reg [DATA_WIDTH*2-1:0] operand_se [N-1:0];
    reg [DATA_WIDTH-1:0] alu_result [N-1:0];
    reg [DATA_WIDTH-1:0] alu_add [N-1:0];
    reg [DATA_WIDTH-1:0] alu_mul [N-1:0];
    reg [DATA_WIDTH*4-1:0] alu_mul_wide [N-1:0];
    reg [DATA_WIDTH-1:0] alu_sub [N-1:0];
    reg [DATA_WIDTH-1:0] alu_max [N-1:0];
    reg [7:0] byte_counter=0;

    parameter LATENCY = 2;
    parameter RAM_LATENCY = LATENCY-1;
    parameter MEM_WIDTH = N*DATA_WIDTH;

    integer i;

    //-------------Code Start-----------------

    // Instantiate memory to implement queue
    wire [$clog2(VVVRF_SIZE)-1:0] mem_address_a;
    reg [$clog2(VVVRF_SIZE)-1:0] mem_address_b=0;
    reg mem_write_enable_a = 1'b0;
    reg mem_write_enable_b;
    wire [MEM_WIDTH-1:0] mem_in_a;
    reg [MEM_WIDTH-1:0] mem_in_b;
    wire [MEM_WIDTH-1:0] mem_out_a;
    wire [MEM_WIDTH-1:0] mem_out_b;
    ram_dual_port vvrf (
      .clk( clk ),
      .clken( 1'b1 ),
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
    defparam vvrf.width_a = MEM_WIDTH;
    defparam vvrf.width_b = MEM_WIDTH;
    defparam vvrf.widthad_a = $clog2(VVVRF_SIZE);
    defparam vvrf.widthad_b = $clog2(VVVRF_SIZE);
    defparam vvrf.width_be_a = 1;
    defparam vvrf.width_be_b = 1;
    defparam vvrf.numwords_a = VVVRF_SIZE;
    defparam vvrf.numwords_b = VVVRF_SIZE;
    defparam vvrf.latency = RAM_LATENCY;
    defparam vvrf.init_file = "vvrf.mif";

    always @(posedge clk) begin

      if (tracing==1'b1) begin
        // Logic for output
        vector_out <= valid_result;
        valid_out <= valid_in_delay;
        eof_out <= eof_in_delay;
        bof_out <= bof_in_delay;
        chainId_out <= chainId_in_delay;
      end
      else begin
        valid_out<=0;
        if (configId==PERSONAL_CONFIG_ID) begin
          byte_counter<=byte_counter+1;
          if (byte_counter<MAX_CHAINS)begin
            firmware_op[byte_counter]=configData;
          end
          else if (byte_counter<MAX_CHAINS*2)begin
            firmware_addr_rd[byte_counter]=configData;
          end
          else if (byte_counter<MAX_CHAINS*3)begin
            firmware_cond[byte_counter]=configData;
          end
          else if (byte_counter<MAX_CHAINS*4)begin
            firmware_cache[byte_counter]=configData;
          end
          else if (byte_counter<MAX_CHAINS*5)begin
            firmware_cache_addr[byte_counter]=configData;
          end
          else if (byte_counter<MAX_CHAINS*6)begin
            firmware_minicache[byte_counter]=configData;
          end
          else if (byte_counter<MAX_CHAINS*7)begin
            firmware_cache_cond[byte_counter]=configData;
          end
        end
        else begin
          byte_counter<=0;
        end
      end

      // Delay values until we can read the value to perform the op
      valid_in_delay <= valid_in;
      valid_in_delay_2 <= valid_in_delay;
      vector_in_delay <= vector_in; 
      firmware_cond_delay <= firmware_cond[chainId_in];
      firmware_cache_cond_delay <= firmware_cache_cond[chainId_in];
      firmware_op_delay <= firmware_op[chainId_in];
      firmware_cache_delay <= firmware_cache[chainId_in];
      firmware_cache_delay_2 <= firmware_cache_delay;
      firmware_cache_addr_delay <= firmware_cache_addr[chainId_in];
      firmware_cache_addr_delay_2 <= firmware_cache_addr_delay;
      firmware_minicache_delay <= firmware_minicache[chainId_in];
      firmware_minicache_delay_2 <= firmware_minicache_delay;
      eof_in_delay <= eof_in;
      bof_in_delay <= bof_in;
      chainId_in_delay <= chainId_in;

      // Save values into mini cache
      if (firmware_minicache_delay[1]==1'b1 & valid_in_delay) begin
        mini_cache <= valid_result;
      end
    end

    // Perform ALU ops
    always @(*) begin
      // First, check if I'm reading from mini cache
      if (firmware_minicache_delay[0]==1'b1) begin
        operator = mini_cache;
      end
      else begin
        operator = vector_in_delay;
      end
      // Select if I'm reading from memory or using value I just calculated (to avoid read after write conflicts in the cache)
      if (firmware_cache_delay_2 && valid_in_delay_2 && firmware_cache_addr_delay_2==firmware_cache_addr_delay) begin
        operand = vector_out;
      end
      else begin
        operand = {>>{mem_out_a}};
      end

      // Math for integer data type
      if (DATA_TYPE==0) begin
        for(i=0; i<N; i=i+1) begin
          alu_add[i] = operator[i] + operand[i];
          alu_mul[i] = operator[i] * operand[i];
          alu_sub[i] = operator[i] - operand[i];
          if (operator[i]>operand[i]) begin
            alu_max[i] = operator[i];
          end
          else begin
            alu_max[i] = operand[i];
          end
        end
      end
      // Math for fixed point data type
      else begin
        for(i=0; i<N; i=i+1) begin
          alu_add[i] = operator[i] + operand[i];
          operator_se[i] =  { {DATA_WIDTH{operator[i][DATA_WIDTH-1]}}, operator[i][DATA_WIDTH-1:0] };
          operand_se[i] = { {DATA_WIDTH{operand[i][DATA_WIDTH-1]}}, operand[i][DATA_WIDTH-1:0] };
          alu_mul_wide[i] = (operator_se[i] * operand_se[i]);
          alu_mul[i]=alu_mul_wide[i]>>(DATA_WIDTH/2);
          alu_sub[i] = operator[i] - operand[i];
          if (operator[i][DATA_WIDTH-1]==operand[i][DATA_WIDTH-1]) begin
            if (operator[i]>operand[i] ) begin
              alu_max[i] = operator[i];
            end
            else begin
              alu_max[i] = operand[i];
            end
          end
          else begin
            if (operator[i][DATA_WIDTH-1]==0) begin
              alu_max[i] = operator[i];
            end
            else begin
              alu_max[i] = operand[i];
            end
          end
        end
      end

      case (firmware_op_delay)
        0 : alu_result = operator;
        1 : alu_result = alu_add;
        2 : alu_result = alu_mul;
        3 : alu_result = alu_sub;
        default : alu_result = alu_max;
      endcase

      // Only perform operation if condition is valid
      // none=0, last=1, notlast=2, first=3, notfirst=4
      
      if ( (firmware_cond_delay==8'd0) | 
           (firmware_cond_delay[0] & eof_in_delay[0]==1'b1) | 
           (firmware_cond_delay[1] & eof_in_delay[0]==1'b0) | 
           (firmware_cond_delay[2] & bof_in_delay[0]==1'b1) | 
           (firmware_cond_delay[3] & bof_in_delay[0]==1'b0) | 
           (firmware_cond_delay[4] & eof_in_delay[1]==1'b1) | 
           (firmware_cond_delay[5] & eof_in_delay[1]==1'b0) | 
           (firmware_cond_delay[6] & bof_in_delay[1]==1'b1) | 
           (firmware_cond_delay[7] & bof_in_delay[1]==1'b0) 
           ) begin
        cond_valid = 1'b1;
      end
      else begin
        cond_valid = 1'b0;
      end

      valid_result = cond_valid ? alu_result : operator;

    end

    //Logic for caching
    always @(*) begin 

      if ( (firmware_cache_cond_delay==8'd0) | 
           (firmware_cache_cond_delay[0] & eof_in_delay[0]==1'b1) | 
           (firmware_cache_cond_delay[1] & eof_in_delay[0]==1'b0) | 
           (firmware_cache_cond_delay[2] & bof_in_delay[0]==1'b1) | 
           (firmware_cache_cond_delay[3] & bof_in_delay[0]==1'b0) | 
           (firmware_cache_cond_delay[4] & eof_in_delay[1]==1'b1) | 
           (firmware_cache_cond_delay[5] & eof_in_delay[1]==1'b0) | 
           (firmware_cache_cond_delay[6] & bof_in_delay[1]==1'b1) | 
           (firmware_cache_cond_delay[7] & bof_in_delay[1]==1'b0) 
           ) begin
        cache_cond_valid = 1'b1;
      end
      else begin
        cache_cond_valid = 1'b0;
      end

      mem_in_b =  {>>{valid_result}};
      mem_write_enable_b = firmware_cache_delay & valid_in_delay & cache_cond_valid;
      mem_address_b = firmware_cache_addr_delay;
    end
 
  assign mem_address_a = firmware_addr_rd[chainId_in];
 endmodule 