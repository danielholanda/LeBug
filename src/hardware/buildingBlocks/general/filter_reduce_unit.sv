 //-----------------------------------------------------
 // Design Name : Filter Reduce Unit (Fiter Unit + Matrix Vector Reduce)
 // Function    : Filters vector into a matrix. Then reduces by adding one of the axis
 //-----------------------------------------------------

 module  filterReduceUnit #(
  parameter N=8,
  parameter M=8,
  parameter DATA_WIDTH=32,
  parameter MAX_CHAINS=4,
  parameter PERSONAL_CONFIG_ID=0,
  parameter FUVRF_SIZE=4,
  parameter DATA_TYPE=0,
  parameter [7:0] INITIAL_FIRMWARE_FILTER_OP    [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_FILTER_ADDR  [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_REDUCE_AXIS  [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}}
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
    parameter LATENCY = 2;
    parameter RAM_LATENCY = LATENCY-1;
    parameter MEM_WIDTH = M*DATA_WIDTH;
    parameter FRU_WIDTH = $clog2(N+1);
    parameter reduce_delays = 2;

    reg [7:0] firmware_filter_op     [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_FILTER_OP;
    reg [7:0] firmware_filter_addr   [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_FILTER_ADDR;
    reg [7:0] firmware_reduce_axis   [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_REDUCE_AXIS;

    reg valid_in_delay = 1'b0;
    reg [1:0] eof_in_delay = 2'b00;
    reg [1:0] bof_in_delay = 2'b00;
    reg [DATA_WIDTH-1:0] vector_in_delay [N-1:0];
    reg [$clog2(MAX_CHAINS)-1:0] chainId_in_delay=0;
    reg [7:0] firmware_filter_op_delay;
    reg valid_in_delay_variable [reduce_delays:0];// = 1'b0;
    reg [1:0] eof_in_delay_variable [reduce_delays:0];//= 2'b00;
    reg [1:0] bof_in_delay_variable [reduce_delays:0];//= 2'b00;
    reg [DATA_WIDTH-1:0] vector_in_delay_variable [reduce_delays:0] [N-1:0];
    reg [$clog2(MAX_CHAINS)-1:0] chainId_in_delay_variable [reduce_delays:0];//=0;
    reg [7:0] firmware_filter_op_delay_variable [reduce_delays:0];
    reg [DATA_WIDTH-1:0] operand [M-1:0];
    reg [DATA_WIDTH-1:0] selected_operand;
    reg filter_result [M-1:0] [N-1:0];
    reg reduce_input [N-1:0] [N-1:0];
    reg reduce_input_delay [reduce_delays:0] [N-1:0] [N-1:0];
    reg [FRU_WIDTH-1:0] reduce_result [N-1:0];
    reg [DATA_WIDTH-1:0] reduce_result_wide [N-1:0];
    reg [7:0] firmware_reduce_axis_delay;
    reg [7:0] byte_counter=0;
    reg [7:0] FRU_reconfig_byte_counter=0;
    reg [$clog2(FUVRF_SIZE)-1:0] FRU_reconfig_M_counter=0;
    reg [M*DATA_WIDTH-1:0] FRU_reconfig_vector =0;

    integer i,j,k;

    reg [9:0] count;
    initial begin
      count = 0;
      for (i=0;i<reduce_delays;i=i+1)
        valid_in_delay_variable[i] = 1'b0;
        eof_in_delay_variable[i]=2'b00;
        bof_in_delay_variable[i]=2'b00;
        chainId_in_delay_variable[i]=0;
    end

    genvar g;

    //-------------Code Start-----------------

    // Instantiate memory to implement queue
    reg [$clog2(FUVRF_SIZE)-1:0] mem_address_a=0;
    reg [$clog2(FUVRF_SIZE)-1:0] mem_address_b=0;
    reg mem_write_enable_a=0;
    reg mem_write_enable_b;
    reg [MEM_WIDTH-1:0] mem_in_a =0;
    reg [MEM_WIDTH-1:0] mem_in_b;
    wire [MEM_WIDTH-1:0] mem_out_a;
    wire [MEM_WIDTH-1:0] mem_out_b;
    ram_dual_port furf (
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
    defparam furf.width_a = MEM_WIDTH;
    defparam furf.width_b = MEM_WIDTH;
    defparam furf.widthad_a = $clog2(FUVRF_SIZE);
    defparam furf.widthad_b = $clog2(FUVRF_SIZE);
    defparam furf.width_be_a = 1;
    defparam furf.width_be_b = 1;
    defparam furf.numwords_a = FUVRF_SIZE;
    defparam furf.numwords_b = FUVRF_SIZE;
    defparam furf.latency = RAM_LATENCY;
    defparam furf.init_file = "furf.mif";

    always @(posedge clk) begin

      if (tracing==1'b1) begin
        // Logic for output
        vector_out <= firmware_filter_op_delay_variable[reduce_delays]==8'b1 ? reduce_result_wide : vector_in_delay_variable[reduce_delays];
        valid_out <= valid_in_delay_variable[reduce_delays];
        eof_out <= eof_in_delay_variable[reduce_delays];
        bof_out <= bof_in_delay_variable[reduce_delays];
        chainId_out <= chainId_in_delay_variable[reduce_delays];

      end
      else begin // If we are not tracing, we are reconfiguring the instrumentation
        valid_out<=0;
          if (configId==PERSONAL_CONFIG_ID) begin
            byte_counter<=byte_counter+1;
            if (byte_counter<MAX_CHAINS)begin
              firmware_filter_op[byte_counter]<=configData;
            end
            else if (byte_counter<MAX_CHAINS*2)begin
              firmware_filter_addr[byte_counter]<=configData;
            end
            else if (byte_counter<MAX_CHAINS*3)begin
              firmware_reduce_axis[byte_counter]<=configData;
            end
            else if (byte_counter<MAX_CHAINS*3+FUVRF_SIZE*(M*DATA_WIDTH/8)) begin
              if (M*DATA_WIDTH<=8) begin
                FRU_reconfig_vector<=configData;
              end
              else begin
                FRU_reconfig_vector<={FRU_reconfig_vector[M*DATA_WIDTH-8-1:0],configData};
              end
              if (FRU_reconfig_byte_counter==M*DATA_WIDTH/8-1) begin
                FRU_reconfig_byte_counter<=0;
                FRU_reconfig_M_counter<=FRU_reconfig_M_counter+1;
                mem_write_enable_b<=1;
                mem_address_b<=FRU_reconfig_M_counter;
                mem_in_b<=FRU_reconfig_vector;
              end
              else begin 
                mem_write_enable_b<=0;
                FRU_reconfig_byte_counter<=FRU_reconfig_byte_counter+1;
              end
            end
          end
          else begin
            byte_counter<=0;
            mem_write_enable_b<=0;
            FRU_reconfig_byte_counter<=0;
            FRU_reconfig_M_counter<=0;
          end
        end

        // Delay values until we can read the value to perform the op
        valid_in_delay <= valid_in;
        vector_in_delay <= vector_in; 
        firmware_filter_op_delay <= firmware_filter_op[chainId_in];
        firmware_reduce_axis_delay <= firmware_reduce_axis[chainId_in];
        eof_in_delay <= eof_in;
        bof_in_delay <= bof_in;
        chainId_in_delay <= chainId_in;
        reduce_input_delay[0]<=reduce_input;
        firmware_filter_op_delay_variable[0]<=firmware_filter_op_delay;
        for (k=0;k<reduce_delays;k++) begin
          reduce_input_delay[k+1]<=reduce_input_delay[k];
          firmware_filter_op_delay_variable[k+1]<=firmware_filter_op_delay_variable[k];
          vector_in_delay_variable[k+1]<=vector_in_delay_variable[k];
          valid_in_delay_variable[k+1]<=valid_in_delay_variable[k];
          eof_in_delay_variable[k+1]<=eof_in_delay_variable[k];
          bof_in_delay_variable[k+1]<=bof_in_delay_variable[k];
          chainId_in_delay_variable[k+1]<=chainId_in_delay_variable[k];
        end
        vector_in_delay_variable[0]<=vector_in_delay;
        valid_in_delay_variable[0]<=valid_in_delay;
        eof_in_delay_variable[0]<=eof_in_delay;
        bof_in_delay_variable[0]<=bof_in_delay;
        chainId_in_delay_variable[0]<=chainId_in_delay;
      end

    // Logic for filter unit
    always @(*) begin
      operand = {>>{mem_out_a}};
      for(i=0; i<N; i=i+1) begin
        for(j=0; j<M; j=j+1) begin
          if (j<M-1) begin
            selected_operand=operand[j+1];
          end
          else if (M==1) begin
            // If M==1 this is a very special scenario. In this scenario, we just assume that the distance between bins is constant (hardcoded 1 here)
            selected_operand=operand[j]+1;
          end
          else begin
            // In order to be able to split the distribution into many Ms we assume that the steps between bins is constant for the last bin of every M
            selected_operand=(operand[j]+operand[1]-operand[0]);
          end
          filter_result[j][i] = vector_in_delay[i]>operand[j] & vector_in_delay[i]<=selected_operand;
        end
      end
    end

    // Logic for reduce unit
    always @(*) begin
      // Reduce along N axis
      if (firmware_reduce_axis_delay==8'd2) begin
        for(i=0; i<N; i=i+1) begin
          for(j=0; j<N; j=j+1) begin
            if (i<M) begin
              reduce_input[i][j]=filter_result[i][j];
            end
            else begin
              reduce_input[i][j]=0;
            end
          end
        end
      end
      // Reduce along M axis
      else begin
        for(i=0; i<N; i=i+1) begin
          for(j=0; j<N; j=j+1) begin
            if (j<M) begin
              reduce_input[i][j]=filter_result[j][i];
            end
            else begin
              reduce_input[i][j]=0;
            end
          end
        end
      end

      mem_address_a = firmware_filter_addr[chainId_in];
    end



    // Logic for reduce unit
    generate 
      for (g=0;g<N;g++) begin
        adderTree1Bit #(.N(N))adder_tree_inst(.vector(reduce_input_delay[reduce_delays][g]), .result(reduce_result[g]));
      end
    endgenerate

    // Make data type adjustments
    always @(*) begin
      if (DATA_TYPE==0) begin // Integer data type
        // Pad result with zeros
        for (i=0;i<N;i++) begin
          reduce_result_wide[i]=reduce_result[i]+{DATA_WIDTH{1'b0}};
        end
      end
      else begin //Fixed point
        for (i=0;i<N;i++) begin
          reduce_result_wide[i]=reduce_result[i]<<DATA_WIDTH/2+{DATA_WIDTH{1'b0}};
        end
      end

    end
 
 endmodule 