import rclpy
from rclpy.node import Node
from moveit_msgs.msg import PositionIKRequest, JointConstraint
from moveit_interface.srv import Goal, Initial
from .quaternion import euler_quaternion
from moveit_msgs.msg import PositionIKRequest
from moveit_msgs.srv import GetPositionIK
from enum import Enum, auto


class State(Enum):
    """ The 3 states of the system.
        Determines what the main timer function and other callback should be doing on each iteration
        depending on the state
    """
    INITIAL = auto(),
    GETTING = auto(),
    GOTIT = auto()

class InverseKinematics(Node):
    def __init__(self):
        super().__init__('inverse_kinematics')

        self.computeik_done = 0
        self.joint_constr_list = []

        self.state = State.INITIAL
        self.goal = self.create_service(Goal, "/goal_service", self.goal_service)
        self.initial = self.create_service(Initial, "/initial_service", self.initial_service)
        self.ik_client = self.create_client(GetPositionIK, "compute_ik")
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.rq = PositionIKRequest()

    def load_callback(self):
        self.rq.group_name='panda_arm'
        self.rq.robot_state.joint_state.header.stamp=self.get_clock().now().to_msg()
        self.rq.robot_state.joint_state.header.frame_id='panda_link0'
        self.rq.robot_state.joint_state.name=['panda_joint1', 'panda_joint2', 'panda_joint3',
                                              'panda_joint4', 'panda_joint5', 'panda_joint6',
                                              'panda_joint7' ]
        self.rq.robot_state.joint_state.position=[0.0,-0.70, 0.0, -2.35, 0.0, 1.57, 0.79]
        self.rq.robot_state.multi_dof_joint_state.header.stamp=self.get_clock().now().to_msg()
        self.rq.robot_state.multi_dof_joint_state.header.frame_id='panda_link0'
        self.rq.robot_state.multi_dof_joint_state.joint_names=['panda_joint1', 'panda_joint2', 
                                                                'panda_joint3', 'panda_joint4', 
                                                                'panda_joint5', 'panda_joint6',
                                                                'panda_joint7' ]
        self.rq.robot_state.is_diff=False
        self.rq.avoid_collisions = True
        self.rq.ik_link_name = 'panda_link8'
        self.rq.pose_stamped.header.stamp = self.get_clock().now().to_msg()
        self.rq.pose_stamped.header.frame_id = 'panda_link0'
        self.rq.pose_stamped.pose.position.x = self.goal_x
        self.rq.pose_stamped.pose.position.y = self.goal_y
        self.rq.pose_stamped.pose.position.z = self.goal_z
        self.rq.pose_stamped.pose.orientation.x = self.goal_ori_x
        self.rq.pose_stamped.pose.orientation.y = self.goal_ori_y
        self.rq.pose_stamped.pose.orientation.z = self.goal_ori_z
        self.rq.pose_stamped.pose.orientation.w = self.goal_ori_w
        self.rq.ik_link_names = ['panda_hand', 'panda_hand_tcp', 'panda_leftfinger', 'panda_link0', 
                                    'panda_link1', 'panda_link2', 'panda_link3', 'panda_link4', 
                                    'panda_link5', 'panda_link6', 'panda_link7', 'panda_link8',
                                    'panda_rightfinger']
        self.rq.pose_stamped_vector = []
        self.rq.timeout.sec = 60
        self.get_logger().info(f'before async')
        self.future = self.ik_client.call_async(GetPositionIK.Request(ik_request=self.rq))


    def goal_service(self, request, response):
        self.state = State.GETTING
        self.goal_x=request.x
        self.goal_y=request.y
        self.goal_z=request.z
        self.goal_roll=request.roll
        self.goal_pitch=request.pitch
        self.goal_yaw=request.yaw
        self.goal_ori_x, self.goal_ori_y, self.goal_ori_z, self.goal_ori_w = euler_quaternion(
                                                    self.goal_roll, self.goal_pitch, self.goal_yaw)
        return response


    def goal_service(self, request, response):
        # self.state = State.GETTING
        self.init_x=request.x
        self.init_y=request.y
        self.init_z=request.z
        self.init_roll=request.roll
        self.init_pitch=request.pitch
        self.init_yaw=request.yaw
        self.ini_ori_x, self.init_ori_y, self.init_ori_z, self.init_ori_w = euler_quaternion(
                                                    self.goal_roll, self.goal_pitch, self.goal_yaw)
        return response


    def timer_callback(self):
        if self.computeik_done == 0:
            if self.future.done():
                self.get_logger().info(f'{self.future.result()}')
                self.ik_result = self.future.result()
                self.computeik_done = 1
        
        if self.computeik_done == 1:
            for i in range(len(self.ik_result.solution.joint_state.name)):
                constraint = JointConstraint()
                constraint.joint_name = self.ik_result.solution.joint_state.name[i]
                constraint.position = self.ik_result.solution.joint_state.position[i]
                constraint.tolerance_above = 0.0001
                constraint.tolerance_below = 0.0001
                constraint.weight=1.0
                self.joint_constr_list.append(constraint)

            self.computeik_done += 1

            print('\njoint constraint list')
            for const in self.joint_constr_list:
                print(const)        
        if self.state == State.GETTING:
            self.load_callback()
            self.state = State.GOTIT
        if self.state == State.GOTIT:
            if self.future.done():
                
                self.get_logger().info(f'{self.future.result()}')
                self.state = State.INITIAL


def IK_entry(args=None):
    rclpy.init(args=args)
    node= InverseKinematics()
    rclpy.spin(node)
    rclpy.shutdown()