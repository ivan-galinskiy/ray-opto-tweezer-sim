# This is the transition to the OOP-based program structure (hopefully more optimized)

# Testing rig
import unittest

# Modules to test
import optical_system as osys

# Auxiliary
import numpy as np
import numpy.linalg as npl

# For integration
import scipy.integrate as si 

# For timing
import datetime as dt

class OpticalSystemIntersectionTestCase(unittest.TestCase):
    def test_intersect_normal(self):
        opt = osys.OpticalSystem(np.array([0,0,0.0]), 1.0, 1.5)
        
        opt._o = np.array([[0.0,0,0]])
        opt._l = np.array([[1.0,0,0]])
        
        angle = opt._intersection_angle()
        
        self.assertAlmostEqual(angle[0], 0)
        
    def test_intersect_normal_offset(self):
        opt = osys.OpticalSystem(np.array([3.0,0,0]), 1.0, 1.5)
        
        opt._o = np.array([[3.0,0,0]])
        opt._l = np.array([[1.0,0,0]])
        
        angle = opt._intersection_angle()
        self.assertAlmostEqual(angle[0], 0)
    
    def test_intersect_normal_inv_director(self):
        opt = osys.OpticalSystem(np.array([3.0,0,0]), 1, 1.5)
        
        opt._o = np.array([[3.0,0,0]])
        opt._l = np.array([[1.0,0,0]])
        
        opt._l = -6 * opt._l
        
        ## Inverting the line director shouldn't have any effect:
        
        angle = opt._intersection_angle()
        self.assertAlmostEqual(angle[0], 0)
        
    def test_intersect_normal_angle_director(self):
        opt = osys.OpticalSystem(np.array([3.0,0,0]), 1, 1.5)
        
        opt._o = np.array([[3.0,0,0]])
        opt._l = np.array([[1.0,1,1]])
        
        angle = opt._intersection_angle()
        self.assertAlmostEqual(angle[0], 0)
        
    def test_intersect_normal_angle_director_external(self):
        # And now let the line hit the sphere normally, but at an angle to an axis
        opt = osys.OpticalSystem(np.array([5.0,0,0]), 1, 1.5)
        
        opt._o = np.array([[0,0,5.0]])
        opt._l = np.array([[1.0,0,-1]])
        
        angle = opt._intersection_angle()
        self.assertAlmostEqual(angle[0], 0, places=5)
        
    def test_intersect_normal_at_zero(self):
        # What happens if the position of the intersection is (0,0,0)?
        opt = osys.OpticalSystem(np.array([1.0,0,0]), 1, 1.5)
        
        opt._o = np.array([[1.0,0,0]])
        opt._l = np.array([[-1.0,1,1]])
        
        angle = opt._intersection_angle()
        self.assertAlmostEqual(angle[0], 0)
        
    def test_intersect_tangent(self):
        # What happens if the ray is exactly tangent to the sphere?
        opt = osys.OpticalSystem(np.array([3.0,0,0]), 1, 1.5)
        
        opt._o = np.array([[4.0,0,10]])
        opt._l = np.array([[0,0,-1.0]])
        
        angle = opt._intersection_angle()
        self.assertAlmostEqual(angle[0], np.pi/2)
        
    def test_intersect_45(self):
        # Here, the ray should intersect the sphere at 45 degrees
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, 1.5)
        
        opt._o = np.array([[0,0,-3.0]])
        opt._l = np.array([[1,0,1.0]])
        
        angle = opt._intersection_angle()
        self.assertAlmostEqual(angle[0], np.pi/4)
        
    def test_intersect_invalid_radius(self):
        ## The system should not accept zero or negative sphere radiuses
        for R in [-1, 0]:
            with self.assertRaises(ValueError):
                opt = osys.OpticalSystem(np.array([4.0,0,0]), R, 1.5)
                
## Testing the helper functions to calculate the angle of refraction and the coefficients of transmission/reflection
class SystemRefractionTestCase(unittest.TestCase):
    def test_snell_normal(self):
        # At normal incidence, the angle stays zero:
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, 1.5)
        r = opt._snell(np.array([0]))
        
        self.assertAlmostEqual(r[0], 0)
        
    def test_snell_tangent(self):
        # At tangent incidence, the refr. angle should be critical:
        nr = 1.5
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, nr)
        r = opt._snell(np.array([np.pi/2]))
        
        self.assertAlmostEqual(np.sin(r)[0], 1/nr)
        
    def test_snell_homogeneous(self):
        # If the relative index is 1, then there should be no change of propagation at all
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, 1)
        
        th = np.array([0, np.pi/3, np.pi/4, np.pi/5])
        
        self.assertTrue(np.allclose(opt._snell(th), th))
            
    def test_fresnel_normal(self):
        # Test Fresnel at normal incidence. It should not depend on the polarization, and the energy must be conserved between the transmittance and reflectance
        # Note that Fresnel only really depends on the relative index.
        # Also note that the polarization is specified as the normalized power of p-polarization (Pp). Then, the power of the s-polarization is simply (1-Pp).
        nr = 1.5
        
        # Length of test sample
        testlen = 20
        
        th = np.zeros(testlen)
        r = np.zeros(testlen)
        Pp = np.linspace(0, 1, testlen)
        
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, nr)
        
        T, R = opt._fresnel(th, r, Pp)
            
        self.assertTrue(np.allclose(T+R, 1))
        self.assertTrue(np.allclose(R, ((1 - nr)/(1 + nr))**2))
            
    def test_fresnel_tangent(self):
        # The reflectivity should be 1 at tangent incidence, regardless of polarization
        nr = 1.5
        
        # Length of test sample
        testlen = 20
        
        th = np.pi/2 * np.ones(testlen)
        r = np.zeros(testlen)
        Pp = np.linspace(0, 1, testlen)
        
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, nr)
        
        r = opt._snell(th)
        
        T, R = opt._fresnel(th, r, Pp)
        
        self.assertTrue(np.allclose(T+R, 1))
        self.assertTrue(np.allclose(R, 1))
            
    def test_fresnel_brewster(self):
        # The reflectivity of a p-polarized ray should be nearly 0 at Brewster's angle
        nr = 1.5
        
        # Length of test sample
        testlen = 20
        
        th = np.arctan(nr) * np.ones(testlen)
        r = np.zeros(testlen)
        Pp = np.ones(testlen)
        
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, nr)
        
        r = opt._snell(th)
        
        T, R = opt._fresnel(th, r, Pp)
        self.assertTrue(np.allclose(R, 0))
        
## Test of a higher-level function that returns the Q-force (explained below) of a single ray incident on a sphere
## The Q force is the force exerted by a single ray, but divided by (P*n_1/c) to not depend on the power of this ray and other factors that will have to be included later (see Ashkin, 1992)
class SphereIntersectionForceTestCase(unittest.TestCase):
    def test_force_normal(self):
        # The ray is normally incident on the sphere
        c = np.array([5.0,0,0])
        R = 1
        o = np.array([[0.0,0,0]])
        l = np.array([[1.0,0,0]])
        
        # This is the relative refractive index of the sphere
        nr = 1.5
        
        # And this is the polarization of the ray in Jones notation
        p = np.array([[1.0,0,0]])
        
        opt = osys.OpticalSystem(c, R, nr)
        opt._c = np.array([c])
        opt._l = l
        opt._o = o
        
        forces = opt._ray_force(p)
        
        # There should be a force towards +x. Moreover, it should more than 0.04 (reflectivity)
        self.assertGreater(forces[0,0], 0.04)
        
        # And the forces in the other directions should be zero
        self.assertTrue(np.allclose(forces[0,1:], 0))
    
    def test_force_sign(self):
        # The ray is a bit displaced to the top
        c = np.array([5.0,0,0])
        R = 1
        o = np.array([[0,0,0.1]])
        l = np.array([[1.0,0,0]])
        
        # This is the relative refractive index of the sphere
        nr = 1.5
        
        # And this is the polarization of the ray in Jones notation
        p = np.array([[1.0,0,0]])
        
        opt = osys.OpticalSystem(c, R, nr)
        opt._c = np.array([c])
        opt._l = l
        opt._o = o
        
        forces = opt._ray_force(p)
        
        # Since the ray will be refracted towards -z, the force should be towards +z
        self.assertGreater(forces[0,2], 0)
        
        # And there should be a force towards +x
        self.assertGreater(forces[0,0], 0)
    
    def test_force_ashkin(self):
        # Test the maximum gradient forces published in Ashkin, 1992
        
        # The origin of the ray will be on the sphere for simpler calculations:
        c = np.array([1.0,0,0])
        R = 1
        o = np.array([[0.0,0,0]])
        
        opt = osys.OpticalSystem(np.array([4.0,0,0]), 1, 1.5)
        opt._c = np.array([c])
        
        # And this is the polarization of the ray in Jones notation (circular)
        p = np.array([[1.0,1j,0]])
        
        data = np.array([
            [1.1, np.sqrt(0.429**2 + 0.262**2), 79*np.pi/180],
            [1.2, np.sqrt(0.506**2 + 0.341**2), 72*np.pi/180],
            [1.4, np.sqrt(0.566**2 + 0.448**2), 64*np.pi/180],
            [1.6, np.sqrt(0.570**2 + 0.535**2), 60*np.pi/180],
            [1.8, np.sqrt(0.547**2 + 0.625**2), 59*np.pi/180],
            [2.0, np.sqrt(0.510**2 + 0.698**2), 59*np.pi/180],
            [2.5, np.sqrt(0.405**2 + 0.837**2), 64*np.pi/180]
            ])
        
        def check(row):
            th = row[2]
            Q = row[1]
            nr = row[0]
            
            opt.set_particle_index(nr)
            
            opt._l = np.array([[np.cos(th), 0, np.sin(th)]])
            forces = opt._ray_force(p)
            
            return np.abs(npl.norm(forces[0,:]) - Q)
            
        res = np.apply_along_axis(check, axis=1, arr=data)
        #print(res)
        self.assertLess(np.max(res), 0.021)
        
## This class tests integration over all the rays coming out of a lens
class TestIntegration(unittest.TestCase):
    
    # Finally, compare the total forces on the sphere to some of Ashkin's results (for Gaussian beam profiles and uniformly-filled objectives as a limit case), but using the class that allows arbitrary functions
    def test_force_gaussian_arbitrary(self):
        f = 1e-3
        
        # A microscope objective with NA = 1.25 (water-immersion). The half-angle of convergence is about 70 degrees
        Rl = f * np.tan(np.arcsin(1.25/1.33))
        
        # A particle of rp=5e-6. Not necessary in this case, but I'll keep for consistency.
        rp = 5e-6
        
        # And the polarization is circular
        p = np.array([1,1j,0])
        
        # Data from Ashkin, 1992
        data = np.array([
            [1.2, 0.00, 0.00, 1.01*rp, -0.276, 2, 1e7*Rl], # Limit of uniformly-filled objective (consistency check)
            [1.2, 0.00, 0.98*rp, 0.00, -0.313, 1, 1e7*Rl], # Limit of uniformly-filled objective (consistency check)
            [1.4, 0.00, 0.00, 0.93*rp, -0.282, 2, 1e7*Rl], # Limit of uniformly-filled objective (consistency check)
            [1.8, 0.00, 0.00, 0.88*rp, -0.171, 2, 1e7*Rl], # Limit of uniformly-filled objective (consistency check)
            
            [1.2, 0.00, 0.00, 1.01*rp, -0.259, 2, 1.7*Rl],
            [1.2, 0.00, 0.98*rp, 0.00, -0.326, 1, 1.7*Rl],
            
            [1.2, 0.00, 0.98*rp, 0.00, -0.349, 1, 1.0*Rl],
            [1.2, 0.00, 0.00, 1.02*rp, -0.225, 2, 1.0*Rl]
            ])
        
        def gaussian_int_pol(r, th, Rl, **kwargs):
            n_rays = len(r)
            # Now we calculate the normalization:
            # The total power passing through the aperture of the lens must be 1. Then, the total power of the full beam is
            P_0 = 1/ (1 - np.exp(-2 * (Rl/kwargs['a'])**2) )
            # The peak intensity is then:
            I_0 = 2*P_0/(np.pi* kwargs['a']**2)
            
            # And the intensity function is
            I = I_0 * np.exp(-2 * (r/kwargs['a'])**2)
            
            # The polarization is fixed
            pol = np.tile(p, (n_rays, 1))
            #pol = np.array([np.cos(th), np.sin(th), np.zeros(r.shape)]).transpose()
            
            return np.hstack([I.reshape(-1,1), pol])
        
        def check(row):
            n = row[0]
            pos = row[1:4]
            targetQ = row[4]
            
            # Force index to check
            i = row[5]
            
            # The Gaussian beam waist (~infinity for uniform filling)
            a = row[6]
            
            opt = osys.OpticalSystemSimpleArbitrary(pos, rp, n, Rl, f, gaussian_int_pol, a=a)
            force = opt.integrate(200, 200)
            
            return np.abs(force[int(i)] - targetQ)
            
        t0 = dt.datetime.now()
        res = np.apply_along_axis(check, axis=1, arr=data)
        t1 = dt.datetime.now()
        print(t1-t0)
        self.assertLess(np.max(res), 0.012)
        
    # Using the arbitrary-intensity case, calculate the forces for donut TEM*01 mode
    def test_force_donut_arbitrary(self):
        f = 1e-3
        
        # A microscope objective with NA = 1.25 (water-immersion). The half-angle of convergence is about 70 degrees
        Rl = f * np.tan(np.arcsin(1.25/1.33))
        
        # A particle of rp=5e-6. Not necessary in this case, but I'll keep for consistency.
        rp = 5e-6
        
        # And the polarization is linear
        p = np.array([0,1,0])
        
        # Data from Ashkin, 1992
        data = np.array([
            [1.2, 0.00, 0.00, 1.00*rp, -0.310, 2, 1.21*Rl],
            [1.2, 0.00, 0.00, 1.01*rp, -0.300, 2, 1.00*Rl],
            [1.2, 0.00, 0.00, 1.01*rp, -0.296, 2, 0.938*Rl],
            [1.2, 0.00, 0.00, 1.01*rp, -0.275, 2, 0.756*Rl],
            
            [1.2, 0.98*rp, 0.00, 0, -0.290, 0, 1.21*Rl],
            [1.2, 0.98*rp, 0.00, 0, -0.296, 0, 1.00*Rl],
            [1.2, 0.98*rp, 0.00, 0, -0.298, 0, 0.938*Rl],
            [1.2, 0.98*rp, 0.00, 0, -0.311, 0, 0.756*Rl],
            ])
        
        def donut_int_pol(r, th, Rl, **kwargs):
            n_rays = len(r)
            a = kwargs['a']
            # Now we calculate the normalization:
            N = np.pi/4 * (a**2 - np.exp(-2 * (Rl/a)**2) * (2*Rl**2 + a**2))
            
            # And the intensity function is
            I = (r/a)**2 * np.exp(-2 * (r/a)**2) / N
            # And the polarization is
            pol = np.tile(p, (n_rays, 1))
            
            return np.hstack([I.reshape(-1,1), pol])
        
        def check(row):
            n = row[0]
            pos = row[1:4]
            targetQ = row[4]
            
            # Force index to check
            i = row[5]
            
            # The Gaussian beam waist (~infinity for uniform filling)
            a = row[6]
            
            opt = osys.OpticalSystemSimpleArbitrary(pos, rp, n, Rl, f, donut_int_pol, a=a)
            force = opt.integrate(200, 200)
            
            return np.abs(force[int(i)] - targetQ)
            
        t0 = dt.datetime.now()
        res = np.apply_along_axis(check, axis=1, arr=data)
        t1 = dt.datetime.now()
        print(t1-t0)
        self.assertLess(np.max(res), 0.006)