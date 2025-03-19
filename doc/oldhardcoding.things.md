in metadata_extractor.js
  if (rich) {
    if (particle.routes?.includes('/(auth)/login')) particle.flows.push('Onboarding: /(auth)/login → discovery');
    if (particle.logic.some(l => l.action.includes('redirect'))) particle.flows.push('Booking: discovery → event → ticket');
    particle.core_rules.forEach(rule => {
      if (rule.condition.includes('capacity')) {
        particle.business_rules.push('Capacity drives stage: Balanced capacity triggers shift');
      } else if (rule.action.includes('redirect')) {
        particle.business_rules.push(`Navigation rule: ${rule.condition} → ${rule.action}`);
      }
    });
    if (particle.depends_on['stripe']) {
      particle.business_rules.push('Revenue split: Organizers and venues divide sales');
    }
  }



  in dependency_tracker.py

      hook_deps = {
        "useRole": "components/Core/Role/hooks/useRole.js",
        "useAuth": "components/Core/Auth/hooks/useAuth.js",
        "useRouter": "expo-router",
        "useSegments": "expo-router",
        "useEventDisplayState": "components/Core/Middleware/state/eventDisplayState.js",
        "useNavigation": "components/Core/Navigation/hooks/useNavigation.js"
    }

